import React, { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface ArduinoData {
  voltage: number;
  resistance: number;
  force: number;
}

const App: React.FC = () => {
  const [data, setData] = useState<ArduinoData>({ voltage: 0, resistance: 0, force: 0 });
  const [isReset, setIsReset] = useState(false);

  useEffect(() => {
    const socket: Socket = io('http://localhost:6000/', {
      transports: ['websocket'],
    });

    // Check if the socket is connected
    socket.on('connect', () => {
      console.log('Socket connected to server');
    });

    // Listen for new data from the server
    socket.on('new_data', (newData: ArduinoData) => {
      console.log('New data received:', newData);
      setData(newData);
      setIsReset(false); // Reset the reset flag when new data is received
    });

    // Listen for reset events
    socket.on('reset_data', () => {
      console.log('Data reset received');
      setData({ voltage: 0, resistance: 0, force: 0 });
      setIsReset(true); // Set reset flag when data is reset
    });

    // Cleanup function to disconnect the socket when component unmounts
    return () => {
      socket.disconnect();
      console.log('Socket disconnected from server');
    };
  }, []);

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', padding: '20px', background: '#f0f0f0', color: '#333' }}>
      <h1>Arduino Data Monitor</h1>
      <div style={{ marginBottom: '20px' }}>
        <p><strong>Voltage:</strong> {data.voltage.toFixed(2)} V</p>
        <p><strong>Resistance:</strong> {data.resistance.toFixed(2)} Ω</p>
        <p><strong>Force:</strong> {data.force > 0 ? data.force.toFixed(2) : 'No hit detected'} N</p>
      </div>
      {isReset && <p style={{ color: 'red' }}>Data has been reset. Awaiting updates...</p>}
    </div>
  );
};

export default App;
