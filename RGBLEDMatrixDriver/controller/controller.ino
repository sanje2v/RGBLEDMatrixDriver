/*
 * This code is to be executed in an BBC micro:bit.
 * NOTE: It may be necessary to readjust stack and heap sizes.
 *       Please refer to https://sanje2v.wordpress.com/ for 
 *       more information.
 * Written by: Sanjeev Sharma. Copyright 2020.
*/

#include "settings.h"
#include "utils.h"

#include "src/Adafruit_NeoPixel_UnmanagedBuffer/Adafruit_NeoPixel_Unmanagedbuf.h"
#include "src/Stopwatch/stopwatch.h"
#include "src/RLE/decompressor.h"


// Static variables
static uint8_t g_pFramesBuffer[TOTAL_FRAMES_BUFFER_SIZE];
static uint8_t g_iCurrentDisplayFrameIndex;
static uint16_t g_iCurrentWriteBytePos;

// Static objects
static Adafruit_NeoPixel_Unmanagedbuf g_sLEDMatrices = Adafruit_NeoPixel_Unmanagedbuf(TOTAL_LEDS,
                                                                                      LED_MATRICES_PWM_PIN,
                                                                                      NEO_GRB + NEO_KHZ800);
static Stopwatch g_sStopwatch = Stopwatch();
static Decompressor g_sFrameDecompressor = Decompressor();

// Function prototypes
void setup();
void loop();
void resetStateAndSendReady(bool);


//////////////////////////// Start here
void setup()
{
  // Initialize random seed generator
  randomSeed(analogRead(RANDOM_GEN_PIN));
  
  // Initialize UART to host
  Serial.begin(UART_BAUD_RATE, SERIAL_8N1);
  
  // Initialize LED controller
  g_sLEDMatrices.begin();
  
  resetStateAndSendReady(true);
}

void loop()
{
  g_sStopwatch.timeit(true);
  
  // Display current frame and increment display frame index
  g_sLEDMatrices.show();

  #ifdef DEBUG
  Serial.print(F("INFO: Displaying 1 frame required (ms): "));
  Serial.println(g_sStopwatch.timeit());
  #endif

  // Saving incoming data to frame buffer
  do
  {
    auto data = Serial.read();
    if (data > -1)  // Check if there is at least one byte of data that has arrived
    {
      g_iCurrentWriteBytePos = g_sFrameDecompressor.feed(static_cast<uint8_t>(data),
                                                         g_pFramesBuffer,
                                                         g_iCurrentWriteBytePos,
                                                         TOTAL_FRAMES_BUFFER_SIZE);

      // Check if the host has sent the special byte sequence asking for a soft reset
      if (g_sFrameDecompressor.gotSoftResetSequence())
      {
        Serial.print(F("INFO: Resetting..."));
        Serial.flush();
        
        resetStateAndSendReady();   // Do soft reset of internal state
        return;                     // Let 'loop()' function be called again from beginning
      }

      // If a complete frame has been received, send host 'SYNC' message to ask for next frame
      if (g_sFrameDecompressor.getTotalBytesDecompressed() == ONE_FRAME_SIZE)
      {
        Serial.print(SYNC_MESSAGE);
        Serial.flush();
      }
      else if (g_sFrameDecompressor.getTotalBytesDecompressed() > ONE_FRAME_SIZE)
      {
        Serial.print(F("ERROR: Received more bytes than required for 1 complete frame."));
        Serial.flush();

        resetStateAndSendReady();   // Do soft reset of internal state
        return;                     // Let 'loop()' function be called again from beginning
      }
    }
  } while(g_sStopwatch.timeit() < TIME_BETWEEN_FRAMES_MS);
  
  g_iCurrentDisplayFrameIndex = incrementFrameDisplayIndex(g_iCurrentDisplayFrameIndex, TOTAL_FRAMES);
  g_sLEDMatrices.setFramePtr(&g_pFramesBuffer[g_iCurrentDisplayFrameIndex]);
}

void resetStateAndSendReady(bool isHardReset)
{
  // Initialize static variables
  g_iCurrentDisplayFrameIndex = 0;
  g_iCurrentWriteBytePos = FRAMES_TO_WRITE_AHEAD * ONE_FRAME_SIZE; // Write 2 frames ahead

  // Reset frame decompressor's soft reset sequence detector's state
  g_sFrameDecompressor.reset();
  
  // Reset frame buffer data and point LED controller to first frame
  if (isHardReset)
    fillFramesBufferForHardReset(&g_pFramesBuffer[0], TOTAL_FRAMES_BUFFER_SIZE);
  else
    fillFramesBufferForSoftReset(&g_pFramesBuffer[0], TOTAL_FRAMES_BUFFER_SIZE);
  g_sLEDMatrices.setPixelsPtr(&g_pFramesBuffer[0]);
  
  // Notify host that this LED matrices controller has been initialized
  clearSerialReceiveBuffer();   // NOTE: Sometimes CPU might send junk bytes in boot. Just to be sure.
  Serial.print(READY_MESSAGE);
  Serial.flush();
}
