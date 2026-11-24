# Rapport de contrôle qualité (`mode=full`, `n=270`, `device=cpu`)

- **Strates :** `{'dans_le_champ__sans_renvoi': 170, 'dans_le_champ__renvoi': 30, 'hors_champ': 50, 'doute': 20}`
- **Origines :** `{'aveugle': 206, 'equipe': 64}`
- **Registres :** `{'soutenu': 54, 'populaire': 122, 'courant': 94}`
- **Multi-articles (`dans_le_champ`) :** `94/200`
- **Fuites lexicales :** `0`
- **Doublons :** `0`
- **Erreurs bloquantes :** `0`

- **Split 70/30 (`random_state=42`) :** `{"validation_total": 189, "test_total": 81, "validation_strata": {"dans_le_champ__renvoi": 21, "dans_le_champ__sans_renvoi": 119, "doute": 14, "hors_champ": 35}, "test_strata": {"dans_le_champ__renvoi": 9, "dans_le_champ__sans_renvoi": 51, "doute": 6, "hors_champ": 15}, "validation_origines": {"aveugle": 144, "equipe": 45}, "test_origines": {"aveugle": 62, "equipe": 19}, "leaked_familles": [], "validation_sha256": "b6bc2935e429557e3bd0df3f8888b4bf108916b81b09d31b9cafa3ea2ca9d775", "test_sha256": "8eb33c71a1651a2f966826550712082030298c178e51cd1d548edfea304c28f2"}`