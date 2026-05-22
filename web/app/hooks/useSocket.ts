// web/app/hooks/useSocket.ts
import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import toast from 'react-hot-toast';

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:5000';

export interface RoomAudioCompletedEvent {
  room_code: string;
  audio_id: number;
  processed_url: string | null;
  transcription: string | null;
  duration_seconds: number;
  filename: string;
}

export const useSocket = () => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socketInstance = io(SOCKET_URL, {
      transports: ['websocket'],
      autoConnect: true,
    });

    socketInstance.on('connect', () => {
      console.log('Connected to WebSocket server');
      setIsConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
      setIsConnected(false);
    });

    socketInstance.on('audio_completed', (data: unknown) => {
      console.log('Audio processing completed:', data);
      const filename = (data as { filename?: string })?.filename || '';
      toast.success(`Áudio ${filename} processado com sucesso!`);
    });

    socketInstance.on('room_audio_completed', (data: RoomAudioCompletedEvent) => {
      console.log('Room audio completed:', data);
      toast.success(`Sala ${data.room_code}: áudio processado!`);
    });

    socketInstance.on('room_closed', (data: { room_code: string }) => {
      toast.error(`Sala ${data.room_code} foi encerrada`);
    });

    /* eslint-disable react-hooks/set-state-in-effect */
    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, []);

  return { socket, isConnected };
};
