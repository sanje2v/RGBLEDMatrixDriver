/*
 * This code is to be executed in an BBC micro:bit.
 * NOTE: It may be necessary to readjust stack and heap sizes.
 *       Please refer to https://github.com/sanje2v/RGBLEDMatrixDriver for 
 *       more information.
 * Written by: Sanjeev Sharma. Copyright 2020.
*/

//#define DEBUG

#include "settings.h"
#include "utils.h"

// Local libraries
#include "src/Adafruit_NeoPixel_UnmanagedBuffer/Adafruit_NeoPixel_Unmanagedbuf.h"
#include "src/stopwatch/stopwatch.h"
#include "src/RLE/decompressor.h"



// Static variables
static uint8_t g_pFramesBuffer[TOTAL_FRAMES_BUFFER_SIZE];
static uint8_t g_iCurrentDisplayFrameIndex;
static uint16_t g_iCurrentWriteBytePos_Red,
                g_iCurrentWriteBytePos_Green,
                g_iCurrentWriteBytePos_Blue;
static uint16_t g_IntervalBetweenFrames;

// Static objects
static Adafruit_NeoPixel_Unmanagedbuf g_sLEDMatrices = Adafruit_NeoPixel_Unmanagedbuf(TOTAL_LEDS,
                                                                                      LED_MATRICES_PWM_PIN,
                                                                                      NEO_GRB + NEO_KHZ800);
static Stopwatch g_sStopwatch = Stopwatch();
static Decompressor g_sFrameDecompressor = Decompressor();

// Function prototypes
void setup();
void loop();
void resetStateAndSendReady(bool, uint16_t=DEFAULT_TIME_BETWEEN_FRAMES_MS);


//////////////////////////// Start here
void setup()
{
  // Initialize random seed
  randomSeed(analogRead(1));
  
  // Initialize UART serial to host
  Serial.begin(SERIAL_BAUD_RATE, SERIAL_8N1);
  
  // Initialize LED controller
  g_sLEDMatrices.begin();
  
  resetStateAndSendReady(true);
}

void loop()
{
  g_sStopwatch.timeit(true);

  // Display current frame and increment display frame index
  // CAUTION: Interrupts are disabled in the following function
  //          so Serial receive is disabled.
  g_sLEDMatrices.show();
  
  g_iCurrentDisplayFrameIndex = (g_iCurrentDisplayFrameIndex + 1) % TOTAL_FRAMES;
  g_sLEDMatrices.setPixelsPtr(&g_pFramesBuffer[g_iCurrentDisplayFrameIndex * ONE_FRAME_SIZE]);

  #ifdef DEBUG
  Serial.print(F("INFO: Displaying 1 frame required (ms): "));
  Serial.println(g_sStopwatch.timeit());
  #endif
  
  // Tell host we are ready to receive frame data
  Serial.print(SYNC_MESSAGE);
  Serial.flush();
  
  // Saving incoming data to frame buffer
  do
  {
    auto data = Serial.read();
    if (data > -1)
    {
      auto data_byte = static_cast<uint8_t>(data);
      
      // Check if the host has sent invalid times repeat sequence asking for a soft reset
      // NOTE: Using special byte, the host can command this controller
      //       to reset while simultenously specify a time between frames
      if (isResetCommand(data_byte))
      {
        Serial.print(F("INFO: Resetting...\r\n"));
        Serial.flush();
        
        resetStateAndSendReady(false,
                               getIntervalInCommand(data_byte));  // Do soft reset of internal state
        return;                                                   // Let 'loop()' function be called again from beginning
      }
      
      g_sFrameDecompressor.feed(data_byte,
                                g_pFramesBuffer,
                                &g_iCurrentWriteBytePos_Red,
                                &g_iCurrentWriteBytePos_Green,
                                &g_iCurrentWriteBytePos_Blue,
                                TOTAL_FRAMES_BUFFER_SIZE);
      
      #ifdef DEBUG
      Serial.print(F("INFO: Total bytes decompressed: "));
      Serial.println(g_sFrameDecompressor.getTotalBytesDecompressed());
      #endif
    }
  } while (g_sStopwatch.timeit() < g_IntervalBetweenFrames);
}

void resetStateAndSendReady(bool isHardReset, uint16_t timeBetweenFrames)
{
  // Initialize static variables
  g_iCurrentDisplayFrameIndex = 0;
  // CAUTION: Because we write directly to frame buffer of WS2812
  //          which expects data to be in GREEN-RED-BLUE order
  g_iCurrentWriteBytePos_Green = FRAMES_TO_WRITE_AHEAD * ONE_FRAME_SIZE; // Write some frames ahead of current display frame
  g_iCurrentWriteBytePos_Red = g_iCurrentWriteBytePos_Green + 1;
  g_iCurrentWriteBytePos_Blue = g_iCurrentWriteBytePos_Red + 1;
  g_IntervalBetweenFrames = timeBetweenFrames;
  
  // Reset frame decompressor's soft reset sequence detector's state
  g_sFrameDecompressor.reset();
  
  // Reset frame buffer data and point LED controller to first frame
  if (isHardReset)
    fillFramesBufferForHardReset(g_pFramesBuffer, TOTAL_FRAMES_BUFFER_SIZE);
  else
    fillFramesBufferForSoftReset(g_pFramesBuffer, TOTAL_FRAMES_BUFFER_SIZE);
  g_sLEDMatrices.setPixelsPtr(&g_pFramesBuffer[0]);
  
  // Notify host that this LED matrices controller has been initialized
  clearSerialReceiveBuffer();   // NOTE: Sometimes motherboard might send junk bytes in boot. Just to be sure.
  Serial.print(READY_MESSAGE);
  Serial.flush();
}
