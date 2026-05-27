import { useEffect, useRef, useState } from "react";

const useCountDown = (time: number, autoStart = false) => {
  const ref = useRef(time);
  const timer = useRef<NodeJS.Timeout | null>(null);
  const [countDown, setCountDown] = useState(0);

  const start = () => {
    if (!timer.current) {
      setCountDown(ref.current);
      timer.current = setInterval(() => {
        setCountDown(pre => {
          if (pre <= 1) {
            stop();
            return 0;
          }
          return pre - 1;
        });
      }, 1000);
    }
  }

  const stop = () => {
    if (!!timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
  }

  useEffect(() => {
    ref.current = time;
    if (autoStart) {
      start();
    }

    return stop;
  }, [time, autoStart]);
  
  return {
    countDown,
    start,
    stop
  };
}

export default useCountDown;