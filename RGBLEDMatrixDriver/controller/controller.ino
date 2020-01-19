/*
 * This code is to be executed in an Arduino. The code was tested in Arduino UNO.
 * Written by: Sanjeev Sharma. Copyright 2020.
 */

#include <SPI.h>

// SETTINGS
#define LED_ROW_ON                                      (byte)0x00    // NOTE: This is valid for EP-005 LED matrix
#define LED_ROW_OFF                                     (byte)0xFF    // NOTE: This is valid for EP-005 LED matrix
#define SERIAL_SPEED_BPS                                115200
#define MAX_FRAME_BUFFER_SIZE                           (1 * 1024)
#define NUM_LED_MATRICES                                4
#define NUM_ROWS_PER_MATRIX                             8
#define NUM_COLORS_PER_ROW_DOT                          3
#define ONE_MATRIX_FRAME_SIZE                           (NUM_ROWS_PER_MATRIX * NUM_COLORS_PER_ROW_DOT)
#define ONE_FRAME_SIZE                                  (NUM_LED_MATRICES * ONE_MATRIX_FRAME_SIZE)
#define MAX_FRAMES                                      uint8_t(MAX_FRAME_BUFFER_SIZE / ONE_FRAME_SIZE)
#define NUM_REDRAW_EACH_FRAME                           100
static const int SLAVE_SELECT_PINS[NUM_LED_MATRICES]  = { 10, 11, 12, 13 };   // CAUTION: Make sure the number of pins match 'NUM_LED_MATRICES'

// Global allocation
static byte g_pFrameBuffer[MAX_FRAME_BUFFER_SIZE];
static int g_FrameBufferSize;
static uint8_t g_CurrentFrameIndex;


void setup()
{
  // Initialize SPI for controlling LEDs and Serial for communicating with master
  SPI.begin();
  Serial.begin(SERIAL_SPEED_BPS);
  Serial.setTimeout(1000);

  // Configure SPI Slave Select pins as output pins and deselected slaves in SPI
  for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
  {
    pinMode(SLAVE_SELECT_PINS[i], OUTPUT);
    digitalWrite(SLAVE_SELECT_PINS[i], HIGH);
  }

  // Fill default pattern for frame buffer
  const uint8_t NUM_DEFAULT_FRAMES = 10;

  for (uint8_t i = 0; i < NUM_DEFAULT_FRAMES; ++i)
  {
    for (uint8_t j = 0; j < NUM_LED_MATRICES; ++j)
    {
      byte *pCurrentMatrixFrameBuffer = &g_pFrameBuffer[(i * ONE_FRAME_SIZE) + (j * ONE_MATRIX_FRAME_SIZE)];
      
      for (uint8_t k = 0; k < NUM_ROWS_PER_MATRIX; ++k)
      {
        for (uint8_t l = 0; l < NUM_COLORS_PER_ROW_DOT; ++l)
        {
          pCurrentMatrixFrameBuffer[k * NUM_COLORS_PER_ROW_DOT + l] = (i < 5 ? LED_ROW_ON : LED_ROW_OFF);
        }
      }
    }
  }
  

  /*byte *pFrameBuffer = g_pFrameBuffer;
  for (uint8_t i = 0; i < ONE_FRAME_SIZE; i += NUM_COLORS_PER_ROW_DOT)
  {
    pFrameBuffer[i+0] = (i % 2 == 0 ? LED_ROW_ON : LED_ROW_OFF);   // Red LED
    pFrameBuffer[i+1] = LED_ROW_OFF; // Blue LED
    pFrameBuffer[i+2] = LED_ROW_OFF; // Green LED
  }

  pFrameBuffer += ONE_FRAME_SIZE;
  for (uint8_t i = 0; i < ONE_FRAME_SIZE; i += NUM_COLORS_PER_ROW_DOT)
  {
    pFrameBuffer[i+0] = LED_ROW_OFF;   // Red LED
    pFrameBuffer[i+1] = (i % 2 == 1 ? LED_ROW_ON : LED_ROW_OFF); // Green LED
    pFrameBuffer[i+2] = (i % 2 == 1 ? LED_ROW_ON : LED_ROW_OFF); // Blue LED
  }*/

  /*for (uint8_t i = 0; i < NUM_DEFAULT_FRAMES; ++i)
  {
    for (uint8_t j = 0; j < ONE_FRAME_SIZE; j += NUM_COLORS_PER_ROW_DOT)
    {
      g_pFrameBuffer[i * NUM_DEFAULT_FRAMES + j + 0] = (i % 2 == 0 ? LED_RGB_ON : LED_RGB_OFF);  // Red LED
      g_pFrameBuffer[i * NUM_DEFAULT_FRAMES + j + 1] = (i % 2 == 0 ? LED_RGB_OFF : LED_RGB_ON);  // Green LED
      g_pFrameBuffer[i * NUM_DEFAULT_FRAMES + j + 2] = (i % 2 == 0 ? LED_RGB_OFF : LED_RGB_ON);  // Blue LED
    }
  }*/
  
  // Set size of frame buffer for default pattern
  g_FrameBufferSize = NUM_DEFAULT_FRAMES * ONE_FRAME_SIZE;
  
  // Point to first frame
  g_CurrentFrameIndex = 0;

  // Notify host that this LED controller has been initialized
  Serial.println(F("INITIALIZED"));
}

void loop()
{
  // If this is the last frame, notify host
  // NOTE: This hint can allow the host to send next set of frames.
  if ((g_CurrentFrameIndex + 1) == uint8_t(g_FrameBufferSize / ONE_FRAME_SIZE))
    Serial.println(F("COMPLETE"));
  
  // Draw current frame
  // NOTE: We redraw each frame multiple times as we cannot use delay (as display state don't hold)
  for (uint8_t t = 0; t < NUM_REDRAW_EACH_FRAME; ++t)
  {
    for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
    {
      byte *pCurrentMatrixFrameBuffer = &g_pFrameBuffer[(g_CurrentFrameIndex * ONE_FRAME_SIZE) + (i * ONE_MATRIX_FRAME_SIZE)];
      
      for (uint8_t j = 0; j < NUM_ROWS_PER_MATRIX; ++j)
      {
        digitalWrite(SLAVE_SELECT_PINS[i], LOW);  // Select a slave LED matrix
  
        for (uint8_t k = 0; k < NUM_COLORS_PER_ROW_DOT; ++k)
        {
          SPI.transfer(pCurrentMatrixFrameBuffer[j * NUM_COLORS_PER_ROW_DOT + k]);
        }
        SPI.transfer(0x01 << j);  // Send row index for current LED matrix
  
        digitalWrite(SLAVE_SELECT_PINS[i], HIGH); // Deselect the selected LED matrix
      }

      // Explicitly need to turn off the last row of LEDs in the matrix
      // before displaying next frame so that unwanted lingering previous
      // data for last row does not remain.
      digitalWrite(SLAVE_SELECT_PINS[i], LOW);
      for (uint8_t k = 0; k < NUM_COLORS_PER_ROW_DOT; ++k)
      {
        SPI.transfer(LED_ROW_OFF);
      }
      SPI.transfer(0x01 << (NUM_ROWS_PER_MATRIX - 1));
      digitalWrite(SLAVE_SELECT_PINS[i], HIGH);
    }
  }

  // Check if there is data available in Serial port from host
  if (Serial.available() > 0)
  {
    uint8_t CurrentFrameIndex = 0;
    
    do
    {
      // Check if max frame memory has exceeded
      if (CurrentFrameIndex == MAX_FRAMES)
      {
        Serial.println(F("ERROR: Too many frames given!"));
        CurrentFrameIndex = 0;
      }
      
      // Read a frame of data
      size_t bytesRead = Serial.readBytes(&g_pFrameBuffer[CurrentFrameIndex * ONE_FRAME_SIZE], ONE_FRAME_SIZE);
      
      if (bytesRead == ONE_FRAME_SIZE)
        Serial.println(F("OK: Received a good frame."));
      else
        Serial.println(F("ERROR: Incorrect sized frame received!"));
        
      // Increment frame index to input new data for new frame, if it does arrive
      ++CurrentFrameIndex;
      
      // Wait to see if more data arrives
      delay(1000);
    } while (Serial.available() > 0);

    // Set new size of frame buffer
    g_FrameBufferSize = CurrentFrameIndex * ONE_FRAME_SIZE;

    // Reset current frame index pointer to first frame
    g_CurrentFrameIndex = 0;
  }
  else
  {
    // Increment current frame index pointer
    g_CurrentFrameIndex = (g_CurrentFrameIndex + 1) % int(g_FrameBufferSize / ONE_FRAME_SIZE);
  }
}
