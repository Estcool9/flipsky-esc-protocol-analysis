# Enregistrement des connexions Qt — analyse ciblée Rizin

Date : 2026-11-22  
Binaire : `Flipsky_ESC_Tool_V1.7_20261029.exe`  
SHA-256 : `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`

## Méthode

Le binaire PE32 x86 a été réouvert dans REA/Ghidra 12.2, puis les vues ciblées Ghidra ont dépassé le délai de réponse. L'analyse a donc été poursuivie avec la commande Rizin intégrée de REA. Une recherche de références après analyse automatique (`aaa`) a relié les chaînes Qt de signal/slot à la fonction native située à VA `0x00483910`.

L'empreinte SHA-256 avant/après les commandes Rizin est restée identique. Aucun octet du binaire n'a été modifié.

## Enregistrements confirmés dans le code

Dans la fonction `0x00483910`, les appels au helper Qt de connexion sont construits avec les signatures legacy de Qt (préfixe `1` = signal, `2` = slot). Les chaînes sont placées dans les arguments de la fonction de connexion.

| Signal | Slot | Adresse de construction observée |
|---|---|---:|
| `1uartPackDataFromESC(QByteArray&)` | `2uartPackDataFromESC(QByteArray&)` | `0x00483cbb`–`0x00483cd6` |
| `1uartCommSendToFtesc(QByteArray&)` | `2sendDataToESC(QByteArray&)` | `0x00483cf0`–`0x00483d0b` |
| `1firmwareVerRec(FTESC_FIRMWARE_NUMBER)` | `2ftescFirmwareVerRec(FTESC_FIRMWARE_NUMBER)` | `0x00483d25`–`0x00483d40` |
| `1ftescMotorSignalSetupReceviedSlot(QString,bool)` | `2ftescMotorSignalReadAck(QString,bool)` | `0x00483d5a`–`0x00483d75` |
| `1ValueSecretKeyCheckedSlot(int)` | `2ftescMotorSignalSecretKeyCheckAck(int)` | `0x00483dc4`–`0x00483ddf` |

Un peu plus tôt dans cette même fonction, la séquence de connexion à `sendDataToESC(QByteArray&)` est également présente ; les chaînes et les arguments montrent un câblage de signaux d'envoi vers le slot de transport.

## Interprétation prudente

- Le binaire utilise explicitement le mécanisme de connexion Qt signal/slot pour les chemins de données UART.
- Le nom `uartPackDataFromESC` apparaît comme un slot de réception de `QByteArray`. Il est cohérent avec une fonction qui reçoit un buffer puis en extrait/traite des données.
- Le chemin `uartCommSendToFtesc` est connecté à `sendDataToESC(QByteArray&)`, ce qui documente un chemin d'émission de données.
- Les callbacks de firmware, de lecture de configuration et de vérification de secret montrent plusieurs sous-flux de communication.

**Cela ne démontre toujours pas** le format du paquet, le CRC, les opcodes, l'endianness, le chiffrement ou l'authentification sur le fil. Les signatures Qt identifient le câblage, pas l'algorithme du slot.

## Prochaine étape

Retrouver les implémentations natives correspondant aux slots en remontant depuis les références de métadonnées Qt et en identifiant les tables de méta-objets / dispatch. Ensuite, analyser les fonctions appelées depuis le slot de réception pour identifier les opérations de buffer, tests de longueur et calculs de checksum. Les résultats doivent être consignés séparément comme preuve observée ou hypothèse.

## Preuve et limites

- La recherche Rizin `izz~uartPackDataFromESC` a trouvé les signatures `1uartPackDataFromESC(QByteArray&)` et `2uartPackDataFromESC(QByteArray&)` dans `.rdata`.
- Après `aaa`, les références à ces signatures pointent vers des instructions qui chargent les adresses dans les arguments de connexion à VA `0x00483cbb` et `0x00483cc7`.
- Le désassemblage local `pd 180 @ 0x00483c90` montre les appels et leurs arguments.
- Les appels indirects au helper Qt ne sont pas renommés ici : son identité exacte et la résolution de tous les pointeurs restent à confirmer.
- La décompilation Ghidra de ces fonctions a expiré pendant cette session ; cette note s'appuie sur le désassemblage Rizin, pas sur du pseudo-code reconstruit.
