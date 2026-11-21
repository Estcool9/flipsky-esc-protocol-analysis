# Journal d'avancement

## 2026-11-22 — État initial consigné

### Réalisé

- Connexion à l'environnement REA par Gateway et identification du service d'analyse actif.
- Récupération du binaire dans l'espace d'analyse ; taille et SHA-256 vérifiés.
- Première classification : PE32 x86 natif, sans runtime .NET détecté.
- Analyse initiale Ghidra et désassemblage ciblé avec Rizin 0.9.1.
- Identification de sections atypiques `.enigma1` et `.enigma2` ; protection/packing suspecté, non confirmé.
- Récupération et validation de 13 ressources XML compressées Zlib.
- Génération reproductible d'un catalogue de 736 lignes, 222 IDs et 13 profils.
- Repérage de la pile Qt 5 / C++ / QML et des modules internes `Flipsky.ftesc.*`.
- Identification des signatures des méthodes de transport et des callbacks realtime.
- Cartographie partielle des connexions Qt UART dans la zone de registration VA `0x00483b90`.
- Création locale des rapports techniques, scripts et catalogue de paramètres.
- Création de ce dépôt GitHub et publication de la documentation de synthèse.

### Non réalisé

- Aucun firmware ESC disponible.
- Aucune capture USB/UART/BLE issue d'une session réelle.
- Corps du parseur et du sérialiseur pas encore intégralement compris.
- Pas de trame complète reconstruite avec framing, longueur, commande, payload et checksum.
- Pas de bibliothèque protocole indépendante.
- Aucun test sur contrôleur physique.

### Découverte de comparaison VESC

Flipsky distingue officiellement FT ESC (famille indépendante) de FSESC (famille VESC). Le namespace `ftesc` présent dans le binaire renforce l'hypothèse que le programme analysé concerne la gamme FT ESC. Cette conclusion reste à relier au modèle ESC exact.

Source : [Flipsky — Differences Between FT ESC and FSESC (2026-01-09)](https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc).

## Règle pour les prochaines sessions

À chaque étape significative, ajouter une entrée datée ici et mettre à jour les pourcentages dans [STATUS.md](STATUS.md). Pour chaque fait, distinguer :
- **confirmé** : démontré par une donnée observable ou une source vérifiable ;
- **probable** : cohérent avec les indices, mais pas encore démontré ;
- **inconnu** : aucune preuve suffisante.
