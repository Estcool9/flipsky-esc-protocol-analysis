# Flipsky ESC Tool — analyse du protocole

Projet de rétro-ingénierie **statique et documentée** d'une application Flipsky de configuration d'ESC. Objectif : comprendre son architecture, ses ressources de paramètres et surtout la communication série avec le contrôleur, puis déterminer ce qui est réutilisable ou non depuis l'écosystème VESC.

> **Statut au 22 novembre 2026 : environ 30 % d'avancement global estimé** vers une compréhension suffisamment complète du protocole pour envisager un client indépendant. Ce chiffre représente une estimation de jalons, pas une mesure scientifique.

## Résultats déjà établis

- Binaire Windows examiné : PE32 x86, natif (pas de CLR/.NET détecté), taille 50 611 200 octets.
- SHA-256 du fichier source examiné : `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`.
- Sections `.enigma1` et `.enigma2` et entropie élevée : protection/packing plausible, sans identification certaine du protecteur ni preuve d'un unpacking réussi.
- Application basée sur Qt 5, C++ et QML ; QtQuick, QtQuick.Controls, QtQuick.Layouts, QtCharts, Qt5SerialPort et Qt5Bluetooth.
- 13 ressources XML compressées Zlib récupérées et validées. Catalogue dérivé : 736 lignes de variantes de profils et 222 IDs distincts.
- Câblage Qt de réception et d'envoi série partiellement cartographié.
- Fonctions de transport identifiées par leurs noms, mais le format exact des trames n'est pas encore compris.

## Avancement estimé

| Volet | Estimation |
|---|---:|
| Inventaire et intégrité du binaire | 100 % |
| Extraction/validation des ressources XML | 100 % |
| Catalogue des paramètres | 100 % |
| Identification de la pile Qt/QML | 80 % |
| Cartographie des signaux UART/Qt | 65 % |
| Analyse des implémentations des fonctions UART | 25 % |
| Format des trames, commandes, CRC et réponses | 5 % |
| Compatibilité VESC documentée | 20 % |
| Client indépendant / émulateur | 0 % |
| Essais sur matériel réel | 0 % |
| **Global estimé** | **~30 %** |

Les pourcentages sont des estimations par jalons, à réviser au fil des preuves. Voir [docs/STATUS.md](docs/STATUS.md), [docs/PROGRESS_LOG.md](docs/PROGRESS_LOG.md) et [docs/QT_CONNECTION_REGISTRATION.md](docs/QT_CONNECTION_REGISTRATION.md).

## Résultats techniques

Signatures retrouvées :
- `lowLevelSendDataToFtesc(QByteArray&)`
- `uartPackDataFromESC(QByteArray&)`
- `uartCommSendToFtesc(QByteArray&)`
- `ftescMotorSignalReadAck(QString,bool)`
- `ftescTopFlowSetupReadAck(QString,bool)`
- `ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)`

Chemin de réception cohérent avec les connexions Qt :
`QSerialPort::readyRead()` → `UartComm::uartDataHandleAvailable()` → `uartPackDataFromESC(...)`.

Ce câblage ne révèle pas encore les octets transmis ni le format de la trame.

## VESC : une distinction à ne pas manquer

Flipsky distingue officiellement les FSESC basés sur VESC des FT ESC développés indépendamment et destinés à Flipsky ESC Tool. Les noms `Flipsky.ftesc.*` dans le binaire sont un indice fort pour la famille FTESC, mais le modèle matériel exact reste à confirmer. Voir [docs/VESC_COMPARISON.md](docs/VESC_COMPARISON.md).

## Prochaines étapes

1. Désassembler les fonctions `uartPackDataFromESC`, `lowLevelSendDataToFtesc` et `uartCommSendToFtesc`.
2. Retrouver les limites de trame, champs longueur, IDs de commande et checksums.
3. Reconstituer les requêtes/réponses et les structures de valeurs.
4. Comparer les résultats au code VESC ouvert, sans présumer de compatibilité.
5. Construire des tests offline avant toute expérimentation matérielle.

## Limites et précautions

Aucun firmware ESC ni capture série réelle n'est disponible pour l'instant. Le catalogue est une description des paramètres contenus dans l'application, **pas** une recommandation de réglage. N'envoyer aucune trame inconnue à un ESC relié à un moteur ; ne pas flasher ou effacer de bootloader pendant l'analyse.

Ce dépôt contient de la documentation de synthèse seulement. L'exécutable, le firmware et les ressources XML extraites n'y sont pas publiés. **Le dépôt est actuellement public** : ne pas y ajouter de binaire, de secret, de capture privée ni de ressource propriétaire sans vérifier les droits de redistribution.

## Sources

- [Flipsky — différences entre FT ESC et FSESC (9 janvier 2026)](https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc)
- [Flipsky — compatibilité FSESC / VESC Tool (27 septembre 2024)](https://flipsky.net/blogs/vesc-tool/tips-for-compatible-fsesc-and-vesc_tool-version)
- [VESC Tool — code source](https://github.com/vedderb/vesc_tool)
- [VESC firmware — code source](https://github.com/vedderb/bldc)
