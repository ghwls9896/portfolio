import 'package:flutter/material.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) => const MaterialApp(home: ChatPage());
}

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});
  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  IO.Socket? socket;
  final messages = <Map<String, dynamic>>[];
  final controller = TextEditingController();

  final roomId = 'room1';
  final userId = 'user_${DateTime.now().millisecondsSinceEpoch}';

  @override
  void initState() {
    super.initState();
    _connect();
  }

  void _connect() {
    socket = IO.io(
      'http://localhost:3000',
      IO.OptionBuilder().setTransports(['websocket']).disableAutoConnect().build(),
    );

    socket!.onConnect((_) {
      print('[socket] connected: ${socket!.id}');
      socket!.emit('join_room', {'roomId': roomId, 'userId': userId});
      setState(() {
        messages.add({'sender': 'system', 'text': 'connected: ${socket!.id}'});
      });
    });

    socket!.onConnectError((e) {
      print('[socket] connect_error: $e');
      setState(() {
        messages.add({'sender': 'system', 'text': 'connect_error: $e'});
      });
    });

    socket!.onError((e) {
      print('[socket] error: $e');
      setState(() {
        messages.add({'sender': 'system', 'text': 'error: $e'});
      });
    });

    socket!.onDisconnect((_) {
      print('[socket] disconnected');
      setState(() {
        messages.add({'sender': 'system', 'text': 'disconnected'});
      });
    });

    socket!.on('message', (data) {
      setState(() {
        messages.add({'sender': data['sender'], 'text': data['text']});
      });
    });

    socket!.connect();
  }

  void _send() {
    final text = controller.text.trim();
    if (text.isEmpty || socket == null) return;

    // 로컬 에코: 최소한 화면엔 바로 보이게
    setState(() {
      messages.add({'sender': userId, 'text': text});
    });

    socket!.emit('message_send', {
      'roomId': roomId,
      'userId': userId,
      'text': text,
    });

    controller.clear();
  }

  @override
  void dispose() {
    socket?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Chat Room')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: messages.length,
              itemBuilder: (_, i) {
                final m = messages[i];
                final isMe = m['sender'] == userId;
                return Align(
                  alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isMe ? Colors.deepPurpleAccent : Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      '${m['sender']}: ${m['text']}',
                      style: TextStyle(color: isMe ? Colors.white : Colors.black),
                    ),
                  ),
                );
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  decoration: const InputDecoration(hintText: '메시지 입력', border: OutlineInputBorder()),
                  onSubmitted: (_) => _send(),
                ),
              ),
              const SizedBox(width: 8),
              IconButton(icon: const Icon(Icons.send), onPressed: _send),
            ]),
          ),
        ],
      ),
    );
  }
}
