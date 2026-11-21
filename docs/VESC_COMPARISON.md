# Comparaison : Flipsky ESC Tool et VESC Tool

**Conclusion actuelle :** l'application examinée ressemble à VESC Tool par sa fonction, son environnement Qt/C++/QML et ses vues de paramètres. Cela ne suffit pas à conclure que le protocole série est identique.

## 1. Distinction publiée par Flipsky

Dans un article daté du **9 janvier 2026**, Flipsky distingue deux familles :

- **FSESC / VESC** : contrôleurs basés sur VESC, configurés avec VESC Tool et dépendants de la version de firmware correspondante.
- **FT ESC / NON-VESC** : gamme développée indépendamment par les ingénieurs Flipsky, annoncée comme compatible uniquement avec Flipsky ESC Tool.

L'article indique que ces gammes et leurs outils ne sont pas interchangeables : [Flipsky — Differences Between FT ESC and FSESC](https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc).

Flipsky publiait déjà en septembre 2024 des consignes de correspondance entre versions de firmware FSESC et versions VESC Tool : [Flipsky — Tips for compatible FSESC and VESC Tool versions](https://flipsky.net/blogs/vesc-tool/tips-for-compatible-fsesc-and-vesc_tool-version).

## 2. Indices dans notre binaire

Le binaire analysé contient les modules et signatures préfixés par `ftesc`, notamment :

- `Flipsky.ftesc.FtescLowLevelFace`
- `Flipsky.ftesc.uartcomm`
- `Flipsky.ftesc.valuesetups`
- `ftescMotorSignalReadAck(...)`
- `ftescGetRealtimeDataOnce(...)`

C'est un indice fort en faveur d'une application de la famille FTESC. Le modèle exact du contrôleur visé reste à confirmer.

## 3. Similarités et niveaux de preuve

| Domaine | Observation | Preuve |
|---|---|---|
| Rôle utilisateur | Configuration d'un contrôleur ESC | Élevée |
| Interface | Application Qt avec paramètres | Élevée |
| Transport | Liaison série et Bluetooth repérées | Élevée |
| Lecture de paramètres | Signaux/slots de lecture et ACK | Élevée |
| Données realtime | Méthodes de demande/réception | Élevée |
| FOC et paramètres moteur | Familles de paramètres présentes | Élevée |
| Format de paquet identique à VESC | Non démontré | Aucune |
| IDs de commande VESC identiques | Non démontré | Aucune |
| CRC / structure de trame VESC identiques | Non démontré | Aucune |

## 4. Références VESC ouvertes

Le code public VESC Tool et le firmware VESC servent de **références de comparaison**, pas de substituts aux preuves tirées du binaire Flipsky :

- [VESC Tool — vescinterface.cpp](https://github.com/vedderb/vesc_tool/blob/master/vescinterface.cpp) : orchestration de connexion et de fonctionnalités selon le firmware détecté.
- [VESC firmware — comm/commands.c](https://github.com/vedderb/bldc/blob/master/comm/commands.c) : traitement des commandes firmware, dont la lecture des valeurs.
- [VESC Tool — dépôt complet](https://github.com/vedderb/vesc_tool).
- [VESC firmware — dépôt complet](https://github.com/vedderb/bldc).

## 5. Test rigoureux de l'hypothèse

1. Identifier le modèle ESC exact auquel l'application est destinée.
2. Analyser le corps de `uartPackDataFromESC` et les fonctions qui l'appellent.
3. Rechercher les constantes de framing et les routines CRC/checksum.
4. Rechercher explicitement les IDs et structures du protocole VESC dans les chemins d'envoi/réception.
5. Comparer les octets construits par l'application avec le code VESC correspondant.
6. Si une capture passive est disponible, comparer des requêtes connues sans injecter de commandes inconnues.

## 6. Conclusion provisoire

L'analogie avec VESC Tool est utile pour guider l'analyse de l'interface et de l'architecture. Elle ne permet pas de supposer la compatibilité du protocole. Si le binaire correspond bien à l'outil FT ESC, les informations publiées par Flipsky suggèrent au contraire un firmware et un protocole distincts de la famille FSESC/VESC.
