/*
 * This code is to be executed in an Arduino. It was tested in Arduino UNO and 
 * intended to drive EP-0075 LED matrices using SPI.
 * Written by: Sanjeev Sharma. Copyright 2020.
 */

#include "settings.h"
#include "utils.h"
#include "decompressor.h"

//#include<avr/wdt.h>
#include <Adafruit_NeoPixel.h>
#ifdef __AVR__
  #include <avr/power.h>
#endif
#include <SPI.h>


// Defines, function shortnames and Constants


// Global allocation
//static char g_pStringBuffer[128];
static uint8_t g_pFramesBuffer[TOTAL_FRAME_BUFFER_SIZE];
static uint8_t g_CurrentDisplayFrameIndex;
static uint16_t g_CurrentWritePos;

//static uint16_t g_NextFrameBufferWriteBytePos;
//static bool g_bResetNowCommand;

// Static objects
static Adafruit_NeoPixel g_sLEDMatrices = Adafruit_NeoPixel(TOTAL_LEDS,
                                                            LED_MATRICES_PWM_PIN,
                                                            NEO_GRB + NEO_KHZ800);
static Decompressor g_sDecompressor = Decompressor();


//////////////////////////// Start here
void setup()
{
  // Initialize random seed generator
  randomSeed(analogRead(RANDOM_GEN_PIN));
  
  // Initialize frame buffer and associated pointer and indices
  fillFrameBufferWithDefaultPattern(g_sLEDMatrices);
  g_CurrentDisplayFrameIndex = 0;
  g_CurrentWritePos = (TOTAL_FRAMES / 4);
  g_sLEDMatrices.setFramePtr(&g_pFramesBuffer[0]);
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
  // Display current frame and increment display frame index
  g_sLEDMatrices.show();
  
  // First, notify host we are ready to receive the next frame
  uint32_t startTimeMs = millis();
  Serial.print(SYNC_MESSAGE);
  Serial.flush();
  
  do
  {
    int data = Serial.read();
    if (data > -1)  // Try decompressing only if there is only valid byte
      g_CurrentWritePos = g_sFrameDecompressor.feed((uint8_t)data, &g_pFramesBuffer[g_CurrentWritePos], TOTAL_FRAME_BUFFER_SIZE);
  } while((millis() - startTimeMs) >= TIME_BETWEEN_FRAMES_MS)
  
  g_CurrentDisplayFrameIndex = incrementFrameDisplayIndex(g_CurrentDisplayFrameIndex, TOTAL_FRAMES);
  g_sLEDMatrices.setFramePtr(&g_pFramesBuffer[g_CurrentDisplayFrameIndex]);
}
