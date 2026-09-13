# Realtime Chat · Flutter × Socket.IO

Flutter 클라이언트와 Node.js 서버를 연결하는 채팅 프로토타입입니다. 방에 입장하면 최근 20개 메시지를 받고, 새 메시지는 같은 방으로 방송됩니다.

## 실행
서버 폴더에서 `npm ci` 후 `node index.js`를 실행합니다. 포트는 3000입니다.
클라이언트 폴더에서 다음 명령으로 플랫폼 파일을 생성하고 실행합니다.
```bash
flutter create . --project-name client
flutter pub get
flutter run -d chrome
```
원본 `lib/main.dart`와 `pubspec.yaml`을 포함하고 플랫폼 자동 생성 파일은 생략했습니다. 클라이언트 주소는 `http://localhost:3000`입니다. 실제 기기에서는 서버 PC 주소를, Android 에뮬레이터에서는 호스트 접근 주소를 설정해야 합니다.

## 이벤트 계약
| 이벤트 | 내용 |
|---|---|
| `join_room` | `roomId`, `userId`로 방 입장 |
| `message_history` | 최근 메시지 수신 |
| `message_send` | 메시지 전송 |

현재 메시지는 서버 메모리에만 저장됩니다. 인증과 영구 저장, 전송량 제한은 구현 범위 밖이며 개발용 CORS 설정을 사용합니다.
