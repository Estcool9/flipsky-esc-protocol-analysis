# Feuille de route technique

## Phase A — Cartographie statique du binaire

- [x] Identifier le format PE, l'architecture et le runtime.
- [x] Vérifier l'empreinte SHA-256 de l'artefact.
- [x] Identifier la pile Qt/C++/QML et les modules chargés.
- [x] Extraire les ressources XML compressées.
- [x] Construire un catalogue de paramètres reproductible.
- [x] Cartographier les principales connexions Qt UART.
- [ ] Désassembler les fonctions UART de lecture et d'envoi.
- [ ] Relier chaque slot de haut niveau à sa fonction de sérialisation.
- [ ] Identifier les tables de constantes, IDs et états de protocole.

## Phase B — Spécification du protocole

- [ ] Identifier les octets de début et de fin de trame.
- [ ] Identifier le champ longueur et son endianess.
- [ ] Identifier le champ commande / opcode.
- [ ] Identifier le format du payload par famille de requête.
- [ ] Retrouver la méthode CRC/checksum et ses paramètres.
- [ ] Décrire fragmentation, timeout, retransmission et erreurs.
- [ ] Documenter la séquence d'identification et d'authentification éventuelle.
- [ ] Séparer les protocoles UART, BLE et CAN s'ils diffèrent.

**Critère de sortie :** spécification étayée par des références au code et des tests reproductibles sur exemples synthétiques ou captures passives.

## Phase C — Comparaison VESC

- [x] Examiner les déclarations officielles Flipsky sur FT ESC vs FSESC.
- [ ] Identifier le modèle exact du contrôleur visé.
- [ ] Comparer les valeurs/opcodes trouvés au code VESC.
- [ ] Marquer chaque élément comme identique, similaire ou incompatible.
- [ ] Ne pas emprunter les valeurs de trame VESC tant qu'elles ne sont pas confirmées dans le binaire Flipsky.

## Phase D — Outils hors matériel

- [ ] Écrire un parseur de trames sans accès série.
- [ ] Ajouter des tests unitaires sur trames synthétiques.
- [ ] Construire un encodeur de requêtes seulement après validation.
- [ ] Créer un simulateur de réponses / ESC virtuel.
- [ ] Ajouter un journal hexadécimal qui masque les éventuels secrets.

## Phase E — Validation sur matériel (plus tard)

- [ ] Obtenir le modèle exact et la révision hardware.
- [ ] Obtenir, si disponible, le firmware correspondant depuis une source légitime.
- [ ] Faire d'abord une capture passive de requêtes/réponses bénignes.
- [ ] Tester en état sûr, sans charge mécanique et sans commande de couple.
- [ ] N'envisager une commande d'écriture qu'après compréhension complète de son effet.
- [ ] Ne pas commencer par le flash, l'effacement du bootloader ou les commandes moteur.

## Ce que l'on peut faire sans firmware ESC

Même sans fichier `.bin`, `.hex` ou `.fw`, il reste possible de poursuivre le désassemblage du binaire de l'application, retrouver le framing et le checksum, comprendre la séquence de lecture et les accusés de réception, développer un parseur offline, préparer des tests de trames synthétiques et comparer les signatures au protocole VESC.

## Éléments qui aideraient s'ils deviennent disponibles

- Modèle exact et révision du contrôleur.
- Version de l'application et du firmware ESC.
- Capture hexadécimale passive d'une simple connexion puis d'une lecture d'informations, avec secrets et données personnelles retirés.
- Firmware obtenu légalement auprès du fabricant ou depuis le support de l'utilisateur.

Aucun de ces éléments n'est bloquant pour continuer l'analyse statique de l'application.
