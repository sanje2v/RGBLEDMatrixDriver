#ifndef UTILS_H
#define UTILS_H

#include "settings.h"
#include "patterns.h"


// Defines, function shortnames and Constants
#define FORCE_INLINE                  __attribute__((always_inline)) inline


FORCE_INLINE void fillFramesBufferForHardReset(uint8_t *pFramesBuffer, uint16_t totalFramesBufferSize)
{
  memset(pFramesBuffer, (0xFF / 2), totalFramesBufferSize); // Turn on all LEDs as half bright white
}

FORCE_INLINE void fillFramesBufferForSoftReset(uint8_t *pFramesBuffer, uint16_t totalFramesBufferSize)
{
  memset(pFramesBuffer, 0x00, totalFramesBufferSize);       // Turn off all LEDs
}

FORCE_INLINE uint8_t incrementFrameDisplayIndex(uint8_t frameIndex, uint8_t totalFrames)
{
  return (frameIndex + 1) % totalFrames;
}

FORCE_INLINE void clearSerialReceiveBuffer()
{
  while (Serial.read() > 0);   // Read and drop bytes in RX buffer
}

/*inline void ReadSerialAndWriteToFrameBuffer()
{
  if (SerialToHost.available())
  {
    g_bResetNowCommand = false;  // If we received more data after a 'reset-kinda' data, it wasn't a RESET command from host
    
    int readBuffer;
    while (readBuffer = SerialToHost.read(), readBuffer >= 0)
    {
      g_pFrameBuffer[g_NextFrameBufferWriteBytePos] = (byte)readBuffer;
      g_NextFrameBufferWriteBytePos = (g_NextFrameBufferWriteBytePos + 1) % TOTAL_FRAME_BUFFER_SIZE;
    }
    
    // Compute position of the closest beginning of the current frame buffer relative to 'g_NextFrameBufferWriteBytePos'
    const uint8_t MAX_BOUND_COMMAND_SIZE_CHECK = 10;
    const uint16_t BytesWrittenInCurrentFrame = (g_NextFrameBufferWriteBytePos % ONE_FRAME_SIZE);
    if ((BytesWrittenInCurrentFrame >= RESET_COMMAND_SIZE) &&
        (BytesWrittenInCurrentFrame < (RESET_COMMAND_SIZE + MAX_BOUND_COMMAND_SIZE_CHECK)))
    {
      const uint16_t CurrentFrameBufferStartBytePos = (g_NextFrameBufferWriteBytePos - BytesWrittenInCurrentFrame);
      byte *const pStartFrameBufferPos = &g_pFrameBuffer[CurrentFrameBufferStartBytePos];
      if (strncmp((const char *)pStartFrameBufferPos, RESET_COMMAND, RESET_COMMAND_SIZE) == 0)
      {
        // We will reset in the next invocation of this function when
        // some time has elasped and if no more data is given
        g_bResetNowCommand = true;
      }
    }
    
    if ((g_NextFrameBufferWriteBytePos % ONE_FRAME_SIZE) == 0)
    {
      SerialToHost.println(F("OK: Received a frame."));
      //SerialToHost.flush();
    }
  }
  else if (g_bResetNowCommand)
  {
    // Host has asked us to reset
    SerialToHost.println(F("INFO: Resetting..."));
    
    // NOTE: We use watchdog timer to reset the system
    //wdt_enable(WDTO_15MS);
    while (true) {} // Let the watchdog timer fire
  }
}*/

#endif
