import React, { useState, useEffect } from "react";
import { Howl } from "howler";
import "./aurdino.css";

interface ArduinoData {
  force: number;
}

const App: React.FC = () => {
  const [forceValue, setForceValue] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [forceAnimation, setForceAnimation] = useState<number>(0);
  const [isFirstDataReceived, setIsFirstDataReceived] = useState<boolean>(false);

  // Define the sound files for different force ranges
  const soundLow = new Howl({
    src: ["sound_low.mp3"],
    volume: 0.5,
    loop: false,
  });

  const soundMedium = new Howl({
    src: ["sound_medium.mp3"],
    volume: 0.5,
    loop: false,
  });

  const soundHigh = new Howl({
    src: ["sound_high.mp3"],
    volume: 0.5,
    loop: false,
  });

  const soundMax = new Howl({
    src: ["sound_max.mp3"],
    volume: 0.5,
    loop: false,
  });

  // Handle force feedback sound based on score range
  const handleForceFeedback = (force: number) => {
    if (force < 400) {
      soundLow.play();
    } else if (force < 600) {
      soundMedium.play();
    } else if (force < 800) {
      soundHigh.play();
    } else {
      soundMax.play();
    }
  };

  const animateForce = (target: number) => {
    let start = forceAnimation;
    let diff = target - start;
    let duration = 2000; // 2 seconds slow increment
    let startTime: number | null = null;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = timestamp - startTime;

      const progressPercentage = Math.min(progress / duration, 1);
      setForceAnimation(start + diff * progressPercentage);

      // Increment the force value
      setForceValue(Math.round(start + diff * progressPercentage));

      if (progress < duration) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  };

  const handleCalculateScore = async () => {
    try {
      const response = await fetch("http://localhost:8000/data");
      const data: ArduinoData = await response.json();
      console.log("📡 Force data received:", data);

      const targetForce = Math.round(data.force * 100); // scale to 600

      if (forceValue !== null && Math.abs(targetForce - forceValue) > 10) {
        setForceValue(targetForce);
        animateForce(targetForce);
        handleForceFeedback(targetForce);
      }
    } catch (error) {
      setError("Error fetching data.");
      console.error("Error fetching data:", error);
    }
  };

  const handleReset = async () => {
    try {
      const response = await fetch("http://localhost:8000/reset", {
        method: "POST",
      });
      const data = await response.json();
      if (data.status === "success") {
        setForceValue(0);
        setForceAnimation(0);
        soundLow.stop();
        soundMedium.stop();
        soundHigh.stop();
        soundMax.stop();
        setIsFirstDataReceived(false);
      }
    } catch (error) {
      setError("Error resetting data.");
      console.error("Error resetting data:", error);
    }
  };

  useEffect(() => {
    // Initial setup or any additional side effects can be done here.
  }, []);

  return (
    <div className="app-container">
      <h1 className="title">Boxing punching machine</h1>
      {error && <p className="error">{error}</p>}

      <div className="force-container">
        <p className="force-text">
          Force: {forceValue !== null ? forceValue : "Waiting for data..."}
        </p>

        <div className="progress-bar-container">
          <div
            className="progress-bar"
            style={{
              width: `${forceAnimation}%`,
              transition: "width 0.1s ease-out",
            }}  
          />
        </div>
      </div>

      <button className="calculate-btn" onClick={handleCalculateScore} disabled={isFirstDataReceived}>
        Calculate My Score
      </button>
      <button className="reset-btn" onClick={handleReset}>
        Reset
      </button>
    </div>
  );
};

export default App;
