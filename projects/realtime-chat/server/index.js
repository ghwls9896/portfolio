const express = require('express');
const http = require('http');
const cors = require('cors');
const { Server } = require('socket.io');

const app = express();
app.use(cors());
app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: '*' }
});

// 방별 메시지 임시 저장 (MVP: 메모리; 나중에 DB로 교체)
const roomMessages = new Map(); // roomId -> [{ sender, text, ts }]

io.on('connection', (socket) => {
  console.log('user connected:', socket.id);

  socket.on('join_room', (data = {}) => {
    const { roomId, userId } = data;
    if (!roomId || !userId) return;

    socket.join(roomId);
    console.log(`${userId} joined room ${roomId}`);

    // 최근 메시지 히스토리(최대 20개) 보내기
    const list = roomMessages.get(roomId) || [];
    socket.emit('message_history', list.slice(-20));
  });

  socket.on('message_send', (payload = {}) => {
    const { roomId, userId, text } = payload;
    if (!roomId || !userId || !text) return;

    // 로그 찍기 (디버그용)
    console.log(`[message_send] room=${roomId} user=${userId} text=${text}`);

    // 메모리 히스토리에 저장
    const list = roomMessages.get(roomId) || [];
    const msg = { sender: userId, text, ts: Date.now() };
    list.push(msg);
    roomMessages.set(roomId, list);

    // 방에 브로드캐스트
    io.to(roomId).emit('message', msg);
  });

  socket.on('disconnect', () => {
    console.log('user disconnected:', socket.id);
  });
});

app.get('/', (req, res) => {
  res.send('Chat server running');
});

server.listen(3000, () => {
  console.log('Server is running on port 3000');
});
