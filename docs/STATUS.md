# État détaillé du projet

**Date de référence : 2026-11-22**  
**Avancement global estimé : ~30 %** du parcours vers une spécification exploitable du protocole et un client indépendant.

## 1. Artefact analysé

| Propriété | Résultat |
|---|---|
| Type | PE32 / x86 |
| Runtime | Pas de CLR/.NET détecté |
| Taille | 50 611 200 octets |
| SHA-256 | `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38` |
| Sections notables | `.enigma1`, `.enigma2` |
| Protection | Entropie élevée et sections atypiques ; protecteur exact non confirmé |
| Outils | Ghidra pour l'analyse initiale, Rizin 0.9.1 pour le désassemblage ciblé |

L'intégrité a été vérifiée avant et après le transfert vers la machine d'analyse. L'exécutable original conservé à la source n'a pas été modifié.

## 2. Ressources et paramètres

- 13 blobs XML compressés Zlib récupérés, décompressés et validés comme XML.
- 736 lignes dans le catalogue de paramètres (les variantes de profils comptent séparément).
- 222 IDs de paramètres distincts.
- Scripts d'extraction et de génération testés pour reproductibilité.
- Formats produits localement : CSV, JSON et JSON des IDs.

Familles de champs : CAN, UART, PPM, ADC, PAS, courants batterie/moteur, eRPM, résistance et inductance de phase, flux, gains FOC, encodeurs, PWM, mesures thermiques et seuils de coupure batterie.

**Limite :** le catalogue décrit les champs et valeurs trouvés dans les ressources logicielles. Il ne démontre pas leur sérialisation sur le port série et ne donne pas de réglages universellement sûrs.

## 3. Architecture repérée

Pile Qt : QtQuick, QtQuick.Controls, QtQuick.Layouts, QtCharts, Qt5SerialPort, Qt5Bluetooth, plus les modules internes :

- `Flipsky.ftesc.FtescLowLevelFace`
- `Flipsky.ftesc.ToolLib`
- `Flipsky.ftesc.uartcomm`
- `Flipsky.ftesc.valuesetups`
- `Flipsky.ftesc.bleuart`

Méthodes et slots nommés :

- `lowLevelSendDataToFtesc(QByteArray&)`
- `uartPackDataFromESC(QByteArray&)`
- `uartCommSendToFtesc(QByteArray&)`
- `ftescMotorSignalReadAck(QString,bool)`
- `ftescTopFlowSetupReadAck(QString,bool)`
- `ftescMotorSignalSecretKeyCheckAck(int)`
- `ftescGetIDResAck(QVector<int>,bool)`
- `ftescAutoGetRealtimeDataAck()`
- `ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)`

## 4. Câblage Qt établi

Une fonction de registration à l'adresse VA `0x00483b90` contient des connexions Qt importantes. Les signatures repérées établissent notamment :

- `QSerialPort::readyRead()` relié à `UartComm::uartDataHandleAvailable()`.
- `QSerialPort::error(QSerialPort::SerialPortError)` relié au slot d'erreur UART.
- `QTimer::timeout()` relié à un slot timer low-level.
- Des signaux de données envoyées reliés à `sendDataToESC(QByteArray&)`.
- Une registration realtime entre `ftescGetRealtimeDataOnce(...)` et un slot de lecture / accusé réception.

Cela prouve le câblage des événements, pas le format des octets transmis.

## 5. Ce qui reste inconnu

Aucune conclusion fiable n'a encore été établie sur les octets de début/fin, la longueur, les IDs de commande, le CRC/checksum, l'endianness, l'échappement, la fragmentation, les retransmissions, les formats de réponse/erreur ou le protocole BLE. Le partage éventuel du protocole avec VESC n'est pas démontré.

## 6. Limites matérielles

Aucun firmware `.bin`, `.hex` ou `.fw` n'a été fourni. Aucun dump de communication série ni capture USB/UART en fonctionnement n'est disponible. Aucun ESC physique n'a été testé pendant cette phase. L'analyse est donc principalement statique et basée sur le binaire de l'application.

## 7. Sécurité

Ne pas déduire un courant, une limite thermique ou un paramètre moteur sûr à partir d'une valeur trouvée dans un XML. Ne pas envoyer de trames inconnues à un ESC connecté à un moteur. Ne pas lancer de mise à jour firmware ni d'effacement bootloader tant que les procédures et risques ne sont pas établis.


## 8. Dernière mise à jour — 2026-11-22

La fonction d'enregistrement Qt à VA `0x00483910` a été désassemblée avec Rizin. Les connexions signal/slot de réception UART, d'envoi, de réception firmware, d'ACK de configuration et de callback de clé sont maintenant consignées dans [QT_CONNECTION_REGISTRATION.md](QT_CONNECTION_REGISTRATION.md). Cela affine le chemin de transport, mais ne révèle toujours pas le format des trames.
