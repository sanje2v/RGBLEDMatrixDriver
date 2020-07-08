/*
 * This code is to be executed in an Arduino. It was tested in Arduino UNO and 
 * intended to drive EP-0075 LED matrices using SPI.
 * Written by: Sanjeev Sharma. Copyright 2020.
 */

#include "settings.h"
#include "utils.h"

#include <decompressor.h>
#include <Adafruit_NeoPixel_Unmanagedbuf.h>


// Defines, function shortnames and Constants


// Global allocation
static uint8_t g_pFramesBuffer[TOTAL_FRAMES_BUFFER_SIZE];
static uint8_t g_CurrentDisplayFrameIndex;
static uint16_t g_CurrentWriteBytePos;

//static uint16_t g_NextFrameBufferWriteBytePos;
//static bool g_bResetNowCommand;

// Static objects
static Adafruit_NeoPixel_Unmanagedbuf g_sLEDMatrices = Adafruit_NeoPixel_Unmanagedbuf(TOTAL_LEDS,
                                                                                      LED_MATRICES_PWM_PIN,
                                                                                      NEO_GRB + NEO_KHZ800);
static Decompressor g_sDecompressor = Decompressor();


//////////////////////////// Start here
void setup()
{
  // Initialize random seed generator
  randomSeed(analogRead(RANDOM_GEN_PIN));
  
  // Initialize frame buffer and associated pointer and indices
  fillFramesBufferForHardReset(g_pFramesBuffer, TOTAL_FRAMES_BUFFER_SIZE);
  g_CurrentDisplayFrameIndex = 0;
  g_CurrentWriteBytePos = static_cast<uint16_t>(2);
  g_sLEDMatrices.setPixelsPtr(&g_pFramesBuffer[0]);
  g_sLEDMatrices.begin();
  
  // Initialize UART to host
  Serial.begin(UART_BAUD_RATE, SERIAL_8N1);
  
  // Notify host that this LED matrices controller has been initialized
  clearSerialReceiveBuffer();
  Serial.print(READY_MESSAGE);
  Serial.flush();
}

void loop()
{
  // First, notify host we are ready to receive the next frame
  Serial.print(SYNC_MESSAGE);
  Serial.flush();
  
  #ifdef DEBUG
  auto _debugstartTimeMs = millis();
  #endif
  
  // Display current frame and increment display frame index
  g_sLEDMatrices.show();

  #ifdef DEBUG
  Serial.print("INFO: Displaying 1 frame required (ms): " + String(millis() - _debugstartTimeMs) + "\n");
  #endif
  
  
  /*auto startTimeMs = millis();
  
  do
  {
    auto data = Serial.read();
    if (data > -1)  // Try decompressing only if there is only valid byte
      g_CurrentWriteBytePos = g_sFrameDecompressor.feed(static_cast<uint8_t>(data),
                                                        &g_pFramesBuffer[g_CurrentWriteBytePos],
                                                        TOTAL_FRAME_BUFFER_SIZE);
  } while((millis() - startTimeMs) < TIME_BETWEEN_FRAMES_MS)
  
  g_CurrentDisplayFrameIndex = incrementFrameDisplayIndex(g_CurrentDisplayFrameIndex, TOTAL_FRAMES);
  g_sLEDMatrices.setFramePtr(&g_pFramesBuffer[g_CurrentDisplayFrameIndex]);*/
}
