/*
 * This code is to be executed in an Arduino. The code was tested in Arduino UNO.
 * Written by: Sanjeev Sharma. Copyright 2020.
 */

#include <SPI.h>

// SETTINGS
#define LED_RGB_ON                                      (byte)0x00    // NOTE: This is valid for EP-005 LED matrix
#define LED_RGB_OFF                                     (byte)0xFF    // NOTE: This is valid for EP-005 LED matrix
#define SERIAL_SPEED_BPS                                115200
#define MAX_FRAME_BUFFER_SIZE                           (1 * 1024)
#define NUM_LED_MATRICES                                4
#define NUM_ROWS_PER_MATRIX                             8
#define NUM_COLORS_PER_ROW_DOT                          3
#define ONE_MATRIX_FRAME_SIZE                           (NUM_ROWS_PER_MATRIX * NUM_COLORS_PER_ROW_DOT)
#define ONE_FRAME_SIZE                                  (NUM_LED_MATRICES * ONE_MATRIX_FRAME_SIZE)
static const int SLAVE_SELECT_PINS[NUM_LED_MATRICES]  = { 10, 11, 12, 13 };   // CAUTION: Make sure the number of pins match 'NUM_LED_MATRICES'

// Global allocation
static byte g_pFrameBuffer[MAX_FRAME_BUFFER_SIZE];
static int g_FrameBufferSize;
static int g_CurrentFrameIndex;


void setup()
{
  // Initialize SPI for controlling LEDs and Serial for communicating with master
  SPI.begin();
  Serial.begin(SERIAL_SPEED_BPS);
  Serial.setTimeout(1000);

  // Configure SPI Slave Select pins as output pins and deselected slaves in SPI
  for (int i = 0; i < NUM_LED_MATRICES; ++i)
  {
    pinMode(SLAVE_SELECT_PINS[i], OUTPUT);
    digitalWrite(SLAVE_SELECT_PINS[i], HIGH);
  }

  // Fill default pattern for frame buffer
  for (int i = 0; i < ONE_FRAME_SIZE; i += NUM_COLORS_PER_ROW_DOT)
  {
    g_pFrameBuffer[i] = (i % 2 == 0 ? LED_RGB_ON : LED_RGB_OFF);   // Red LED
    g_pFrameBuffer[i+1] = (i % 2 == 0 ? LED_RGB_ON : LED_RGB_OFF); // Green LED
    g_pFrameBuffer[i+2] = (i % 2 == 0 ? LED_RGB_ON : LED_RGB_OFF); // Blue LED
  }

  // Set size of frame buffer for default pattern
  g_FrameBufferSize = ONE_FRAME_SIZE;
  
  // Point to first frame
  g_CurrentFrameIndex = 0;
}

void loop()
{
  // Draw current frame
  for (int i = 0; i < NUM_LED_MATRICES; ++i)
  {
    byte *pCurrentMatrixFrameBuffer = &g_pFrameBuffer[(g_CurrentFrameIndex * ONE_FRAME_SIZE) + (ONE_MATRIX_FRAME_SIZE * i)];
    
    for (int j = 0; j < NUM_ROWS_PER_MATRIX; ++j)
    {
      digitalWrite(SLAVE_SELECT_PINS[i], LOW);

      for (int k = 0; k < NUM_COLORS_PER_ROW_DOT; k++)
      {
        SPI.transfer(pCurrentMatrixFrameBuffer[j * NUM_COLORS_PER_ROW_DOT + k]);
      }
      SPI.transfer(0x01 << j);  // Send row index for current LED matrix

      digitalWrite(SLAVE_SELECT_PINS[i], HIGH);
    }
  }

  // Check if there is data available in Serial port from host
  if (Serial.available() > 0)
  {
    g_CurrentFrameIndex = 0;  // NOTE: Reusing local variable
    
    do
    {
      // Read a frame of data
      size_t bytesRead = Serial.readBytes(&g_pFrameBuffer[g_CurrentFrameIndex * ONE_FRAME_SIZE], ONE_FRAME_SIZE);
      
      if (bytesRead == ONE_FRAME_SIZE)
        Serial.println(F("OK: Received a good frame."));
      else
        Serial.println(F("ERROR: Incorrect sized frame received!"));
        
      // Increment frame index to input new data for new frame, if it does arrive
      ++g_CurrentFrameIndex;
      
      // Wait to see if more data arrives
      delay(1000);
    } while (Serial.available() > 0);

    // Set new size of frame buffer
    g_FrameBufferSize = g_CurrentFrameIndex * ONE_FRAME_SIZE;

    // Reset current frame index pointer to first frame
    g_CurrentFrameIndex = 0;
  }
  else
  {
    // Increment current frame index pointer
    g_CurrentFrameIndex = (g_CurrentFrameIndex + 1) % int(g_FrameBufferSize / ONE_FRAME_SIZE);
  }
}
