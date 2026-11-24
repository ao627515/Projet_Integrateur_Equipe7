"""Extracteurs de pages PDF (couche texte intégrée ou OCR local RapidOCR CUDA/CPU)."""

from __future__ import annotations

import gc
import os
import time
from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, as_completed, wait
from pathlib import Path
from typing import Any, Protocol

import pymupdf as fitz

from src.common.io import load_jsonl, register_nvidia_dll_dirs, save_jsonl_atomic
from src.ingestion.cache import PageCache
from src.ingestion.config import ExtractionConfig

# Instance RapidOCR dédiée à chaque processus worker CPU
_WORKER_OCR: Any = None


class PageExtractor(Protocol):
    """Contrat minimal pour tout extracteur de texte page par page depuis un PDF."""

    profile_tag: str

    def extract(self, pdf_path: Path, cache_path: Path) -> list[dict[str, Any]]:
        ...


ExtractorFactory = Callable[[ExtractionConfig], PageExtractor]
_OCR_REGISTRY: dict[str, ExtractorFactory] = {}


def register_extractor(name: str, factory: ExtractorFactory) -> None:
    """Enregistre un moteur d'extraction sous un identifiant utilisable en config/CLI."""
    _OCR_REGISTRY[name.strip().lower()] = factory


def available_extractors() -> list[str]:
    """Retourne les identifiants d'extracteurs actuellement enregistrés."""
    return sorted(_OCR_REGISTRY)


def create_extractor(name: str, config: ExtractionConfig) -> PageExtractor:
    """Instancie l'extracteur enregistré correspondant à `name`."""
    key = name.strip().lower()
    if key not in _OCR_REGISTRY:
        raise ValueError(f"Extracteur inconnu '{name}'. Disponibles : {available_extractors()}")
    return _OCR_REGISTRY[key](config)


def _build_rapidocr_engine(use_cuda: bool = False, threads_per_worker: int = 2) -> Any:
    """Instancie RapidOCR ONNX avec le modèle de reconnaissance latin/français (PP-OCRv5)."""
    from rapidocr import EngineType, LangRec, ModelType, OCRVersion, RapidOCR

    params: dict[str, Any] = {
        "Global.log_level": "warning",
        "Det.engine_type": EngineType.ONNXRUNTIME,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Cls.engine_type": EngineType.ONNXRUNTIME,
        "Rec.lang_type": LangRec.LATIN,
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.model_type": ModelType.MOBILE,
        "EngineConfig.onnxruntime.use_cuda": bool(use_cuda),
    }
    if use_cuda:
        params["EngineConfig.onnxruntime.cuda_ep_cfg.cudnn_conv_algo_search"] = "HEURISTIC"
    else:
        params["EngineConfig.onnxruntime.intra_op_num_threads"] = threads_per_worker
        params["EngineConfig.onnxruntime.inter_op_num_threads"] = 1
    return RapidOCR(params=params)


def _extract_lines_from_ocr(engine: Any, png_bytes: bytes) -> list[str]:
    res = engine(png_bytes)
    if res is None:
        return []
    if hasattr(res, "txts"):
        return [str(t) for t in (res.txts or []) if t]
    if isinstance(res, tuple) and res and res[0]:
        return [item[1] for item in res[0] if len(item) >= 2]
    return []


def detect_onnx_cuda(
    requested: str = "auto", profile_tag: str = "rapidocr_latin_ppocrv5"
) -> tuple[bool, str, Any | None]:
    """Détecte CUDAExecutionProvider actif et retourne l'instance RapidOCR prête à l'emploi."""
    if requested == "cpu":
        return False, "cpu (forcé)", None
    try:
        register_nvidia_dll_dirs()
        import onnxruntime as ort

        if hasattr(ort, "preload_dlls"):
            try:
                ort.preload_dlls(directory="")
            except Exception:
                pass

        if "CUDAExecutionProvider" in ort.get_available_providers():
            import numpy as np

            probe = _build_rapidocr_engine(use_cuda=True)
            probe(np.zeros((64, 64, 3), dtype=np.uint8))
            active: list[str] = []
            for attr in ("text_det", "text_rec"):
                comp = getattr(probe, attr, None)
                for sub in ("session", "infer"):
                    obj = getattr(comp, sub, None)
                    sess = getattr(obj, "session", obj)
                    if sess is not None and hasattr(sess, "get_providers"):
                        active.extend(sess.get_providers())
            if "CUDAExecutionProvider" in active:
                return True, f"cuda (ONNX CUDAExecutionProvider actif, {profile_tag})", probe
            del probe
            gc.collect()
            print(
                "[INFO] CUDAExecutionProvider listé mais inactif (DLL CUDA/cuDNN manquantes) -> repli CPU parallèle sécurisé",
                flush=True,
            )
    except Exception as exc:
        if requested == "cuda":
            print(f"[WARN] CUDA demandé mais indisponible ({exc}) -> repli CPU sécurisé", flush=True)
        else:
            print(f"[INFO] CUDA ONNX indisponible ({exc}) -> exécution CPU parallèle", flush=True)
    return False, "cpu", None


def _init_cpu_worker(threads_per_worker: int = 2) -> None:
    global _WORKER_OCR
    os.environ["OMP_NUM_THREADS"] = str(threads_per_worker)
    os.environ["ORT_INTRA_OP_NUM_THREADS"] = str(threads_per_worker)
    _WORKER_OCR = _build_rapidocr_engine(use_cuda=False, threads_per_worker=threads_per_worker)


def _render_page_png(pdf_str: str, page_num: int, dpi: int) -> tuple[int, bytes, int]:
    doc = fitz.open(pdf_str)
    try:
        page = doc[page_num - 1]
        pix = page.get_pixmap(dpi=dpi)
        return page_num, pix.tobytes("png"), len(page.get_images(full=False))
    finally:
        doc.close()


def _ocr_single_page_cpu(task: tuple[str, int, int, int, str]) -> dict[str, Any]:
    pdf_str, page_num, dpi, retries, profile_tag = task
    last_err = None
    for _ in range(retries):
        try:
            _, png_bytes, img_count = _render_page_png(pdf_str, page_num, dpi)
            lines = _extract_lines_from_ocr(_WORKER_OCR, png_bytes)
            text = "\n".join(lines)
            return {
                "source_pdf": Path(pdf_str).name,
                "page": page_num,
                "mode": f"local_ocr_{profile_tag}_cpu",
                "char_count": len(text.strip()),
                "image_count": img_count,
                "text": text,
            }
        except Exception as exc:
            last_err = exc
    return {
        "source_pdf": Path(pdf_str).name,
        "page": page_num,
        "mode": "local_ocr_error",
        "char_count": 0,
        "image_count": 0,
        "text": "",
        "error": str(last_err),
    }


class EmbeddedTextExtractor:
    """Extrait la couche texte embarquée d'un PDF page par page."""

    profile_tag: str = "embedded_text"

    def __init__(self, force: bool = False) -> None:
        self.force = force

    def extract(self, pdf_path: Path, cache_path: Path) -> list[dict[str, Any]]:
        if cache_path.exists() and not self.force:
            cached = load_jsonl(cache_path)
            if cached:
                print(f"[CACHE] Couche texte déjà extraite : {cache_path} ({len(cached)} pages)", flush=True)
                return cached

        doc = fitz.open(str(pdf_path))
        pages: list[dict[str, Any]] = []
        for idx in range(len(doc)):
            page = doc[idx]
            text = page.get_text("text") or ""
            pages.append(
                {
                    "source_pdf": pdf_path.name,
                    "page": idx + 1,
                    "mode": "embedded_text_layer",
                    "char_count": len(text.strip()),
                    "image_count": len(page.get_images(full=False)),
                    "text": text,
                }
            )
        doc.close()
        save_jsonl_atomic(cache_path, pages)
        print(f"[OK] Extrait {len(pages)} pages (couche texte) -> {cache_path}", flush=True)
        return pages


class RapidOcrExtractor:
    """Exécute RapidOCR local (GPU CUDA à fenêtre RAM bornée ou pool CPU borné) avec cache atomique."""

    def __init__(self, config: ExtractionConfig) -> None:
        self.config = config
        self.profile_tag = config.ocr_profile_tag

    def extract(self, pdf_path: Path, cache_path: Path) -> list[dict[str, Any]]:
        cfg = self.config
        cache = PageCache(cache_path, pdf_path, cfg.dpi, cfg.ocr_profile_tag)
        existing = cache.load_valid_pages(force=cfg.force)

        doc = fitz.open(str(pdf_path))
        total = len(doc) if cfg.max_ocr_pages is None else min(len(doc), cfg.max_ocr_pages)
        doc.close()

        todo = [p for p in range(1, total + 1) if p not in existing]
        if not todo:
            ordered = [existing[i] for i in range(1, total + 1)]
            print(
                f"[CACHE] OCR local valide ({cfg.ocr_profile_tag}, {cfg.dpi} DPI, sha256={cache.pdf_sha[:10]}) : "
                f"{cache_path} ({len(ordered)} pages)",
                flush=True,
            )
            return ordered

        cache.write_meta()
        use_cuda, dev_label, ocr_gpu = detect_onnx_cuda(cfg.device, cfg.ocr_profile_tag)
        results = dict(existing)
        t_start = time.time()

        print(f"[OCR] Device={dev_label} | PDF={pdf_path.name} | Restant={len(todo)}/{total} pages", flush=True)

        try:
            if use_cuda and ocr_gpu is not None:
                self._run_cuda(pdf_path, todo, ocr_gpu, cache, results, t_start)
            else:
                self._run_cpu(pdf_path, todo, cache, results, t_start)
        except KeyboardInterrupt:
            print("\n[INTERRUPT] Arrêt demandé — sauvegarde atomique du cache en cours...", flush=True)
            ordered = cache.save_pages(results)
            print(f"[INTERRUPT] {len(ordered)} pages sauvegardées proprement dans {cache_path}", flush=True)
            raise
        finally:
            if ocr_gpu is not None:
                del ocr_gpu
            gc.collect()

        return cache.save_pages(results)

    def _run_cuda(
        self,
        pdf_path: Path,
        todo: list[int],
        ocr_gpu: Any,
        cache: PageCache,
        results: dict[int, dict[str, Any]],
        t_start: float,
    ) -> None:
        cfg = self.config
        done_cnt = 0
        todo_iter = iter(todo)
        with ThreadPoolExecutor(max_workers=cfg.gpu_render_threads) as render_pool:
            inflight = set()
            for _ in range(min(cfg.max_inflight_gpu_pages, len(todo))):
                p = next(todo_iter, None)
                if p is not None:
                    inflight.add(render_pool.submit(_render_page_png, str(pdf_path), p, cfg.dpi))

            while inflight:
                done_futs, inflight = wait(inflight, return_when=FIRST_COMPLETED)
                for fut in done_futs:
                    page_num, png_bytes, img_count = fut.result()
                    nxt = next(todo_iter, None)
                    if nxt is not None:
                        inflight.add(render_pool.submit(_render_page_png, str(pdf_path), nxt, cfg.dpi))
                    try:
                        lines = _extract_lines_from_ocr(ocr_gpu, png_bytes)
                        text = "\n".join(lines)
                        rec = {
                            "source_pdf": pdf_path.name,
                            "page": page_num,
                            "mode": f"local_ocr_{cfg.ocr_profile_tag}_cuda",
                            "char_count": len(text.strip()),
                            "image_count": img_count,
                            "text": text,
                        }
                    except Exception as exc:
                        rec = {
                            "source_pdf": pdf_path.name,
                            "page": page_num,
                            "mode": "local_ocr_error",
                            "char_count": 0,
                            "image_count": img_count,
                            "text": "",
                            "error": str(exc),
                        }
                    finally:
                        del png_bytes

                    results[page_num] = rec
                    done_cnt += 1
                    if done_cnt % cfg.checkpoint_every_n_pages == 0 or done_cnt == len(todo):
                        cache.save_pages(results)
                        elapsed = max(0.01, time.time() - t_start)
                        speed = done_cnt / elapsed
                        eta = (len(todo) - done_cnt) / max(0.01, speed)
                        print(
                            f"  -> [CUDA] {done_cnt}/{len(todo)} pages (p.{page_num}, {speed:.2f} p/s, ETA ~{eta:.0f}s)",
                            flush=True,
                        )
                    if done_cnt % cfg.gc_every_n_pages == 0:
                        gc.collect()

    def _run_cpu(
        self,
        pdf_path: Path,
        todo: list[int],
        cache: PageCache,
        results: dict[int, dict[str, Any]],
        t_start: float,
    ) -> None:
        cfg = self.config
        cpu_cnt = os.cpu_count() or 4
        safe_workers = max(1, min(cfg.workers, max(1, cpu_cnt // 4), 4))
        threads_per_worker = max(1, min(4, cpu_cnt // safe_workers))
        print(f"  -> [CPU] Pool borné : {safe_workers} workers × {threads_per_worker} threads ONNX", flush=True)

        tasks = [(str(pdf_path), p, cfg.dpi, cfg.ocr_retries_per_page, cfg.ocr_profile_tag) for p in todo]
        done_cnt = 0
        with ProcessPoolExecutor(
            max_workers=safe_workers,
            initializer=_init_cpu_worker,
            initargs=(threads_per_worker,),
        ) as ex:
            futs = [ex.submit(_ocr_single_page_cpu, t) for t in tasks]
            for fut in as_completed(futs):
                rec = fut.result()
                results[rec["page"]] = rec
                done_cnt += 1
                if done_cnt % cfg.checkpoint_every_n_pages == 0 or done_cnt == len(todo):
                    cache.save_pages(results)
                    elapsed = max(0.01, time.time() - t_start)
                    speed = done_cnt / elapsed
                    eta = (len(todo) - done_cnt) / max(0.01, speed)
                    print(
                        f"  -> [CPU] {done_cnt}/{len(todo)} pages (p.{rec['page']}, {speed:.2f} p/s, ETA ~{eta:.0f}s)",
                        flush=True,
                    )


register_extractor("embedded", lambda cfg: EmbeddedTextExtractor(force=cfg.force))
register_extractor("rapidocr", lambda cfg: RapidOcrExtractor(cfg))
