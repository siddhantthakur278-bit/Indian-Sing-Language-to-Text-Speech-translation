"use client";

import React, { useEffect, useState } from "react";

interface AriaAnnouncerProps {
  message: string;
  isAssertive?: boolean;
}

export const AriaAnnouncer: React.FC<AriaAnnouncerProps> = ({ message, isAssertive = false }) => {
  const [announcedMessage, setAnnouncedMessage] = useState<string>("");

  useEffect(() => {
    if (message) {
      setAnnouncedMessage(message);
    }
  }, [message]);

  return (
    <div
      aria-live={isAssertive ? "assertive" : "polite"}
      aria-atomic="true"
      className="sr-only"
    >
      {announcedMessage}
    </div>
  );
};
