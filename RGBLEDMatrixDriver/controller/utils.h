#ifndef UTILS_H
#define UTILS_H

#include "settings.h"


// Defines, function shortnames and Constants
#define FORCE_INLINE                  __attribute__((always_inline)) inline


FORCE_INLINE void fillFramesBufferForHardReset(uint8_t *pFramesBuffer, uint16_t totalFramesBufferSize)
{
  memset(pFramesBuffer, (0xFF / 15), totalFramesBufferSize); // Turn on all LEDs to half brightness white
}

FORCE_INLINE void fillFramesBufferForSoftReset(uint8_t *pFramesBuffer, uint16_t totalFramesBufferSize)
{
  memset(pFramesBuffer, 0x00, totalFramesBufferSize);       // Turn off all LEDs
}

FORCE_INLINE void clearSerialReceiveBuffer()
{
  do
  {
    delay(TIME_DELAY_CLEAR_RX_BUFFER_CHECK_MS);
  } while (Serial.read() > -1);   // Read and drop bytes in RX buffer
}

#endif
