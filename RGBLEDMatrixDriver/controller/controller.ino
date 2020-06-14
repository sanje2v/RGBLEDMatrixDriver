/*
 * This code is to be executed in an Arduino. It was tested in Arduino UNO and 
 * intended to drive EP-0075 LED matrices using SPI.
 * Written by: Sanjeev Sharma. Copyright 2020.
 */

#include "Settings.h"
//#include<avr/wdt.h>
#include <SPI.h>


// Defines and Constants
#define SerialToHost                  Serial
static const int LEDMATRIX_SELECT_PINS[NUM_LED_MATRICES] = _LEDMATRIX_SELECT_PINS;

// Global allocation
static char g_pStringBuffer[128];
static byte g_pFrameBuffer[TOTAL_FRAME_BUFFER_SIZE];
static uint8_t g_CurrentFrameIndex;
static uint16_t g_NextFrameBufferWriteBytePos;
static bool g_bResetNowCommand;


inline void fillFrameBufferWithDefaultPattern()
{
  byte rowStates[ONE_FRAME_SIZE];
  for (uint8_t i = 0; i < TOTAL_FRAMES; ++i)
  {
    /*if (i % 3 == 0)
    {
      for (uint8_t m = 0; m < ONE_FRAME_SIZE; m += NUM_COLORS_PER_ROW_DOT)
      {
        byte rowState = (byte)random(0, 256);  // Random byte value from 0 to 255
        switch (random(3))
        {
          case 0:
            rowStates[m + 0] = rowState;
            rowStates[m + 1] = 0xFF;
            rowStates[m + 2] = 0xFF;
            break;

          case 1:
            rowStates[m + 0] = 0xFF;
            rowStates[m + 1] = rowState;
            rowStates[m + 2] = 0xFF;
            break;

          case 2:
            rowStates[m + 0] = 0xFF;
            rowStates[m + 1] = 0xFF;
            rowStates[m + 2] = rowState;
            break;
        }
      }
    }*/
    
    for (uint8_t j = 0; j < NUM_LED_MATRICES; ++j)
    {
      byte *pCurrentMatrixFrameBuffer = &g_pFrameBuffer[(i * ONE_FRAME_SIZE) + (j * ONE_MATRIX_FRAME_SIZE)];
      
      for (uint8_t k = 0; k < NUM_ROWS_PER_MATRIX; ++k)
      {
        for (uint8_t l = 0; l < NUM_COLORS_PER_ROW_DOT; ++l)
        {
          /*byte rowState;
          if (i < (TOTAL_FRAMES/2))
          {
            rowState = ((l == 1) || (l == 0) ? 0x00 : 0xFF);
          }
          else
          {
            rowState = (l == 2 ? 0x00 : 0xFF);
          }
          pCurrentMatrixFrameBuffer[k * NUM_COLORS_PER_ROW_DOT + l] = rowState;//rowStates[k * NUM_COLORS_PER_ROW_DOT + l];
          */

          byte rowState = 0xFF;
          /*if (k == 1 && l  == 1)
            rowState = 0x3E;
          else
            rowState = 0xFF;*/

          pCurrentMatrixFrameBuffer[k * NUM_COLORS_PER_ROW_DOT + l] = rowState;
        }
      }
    }

    if (i < TOTAL_FRAMES/2)
    {
      g_pFrameBuffer[0] = 0x3E;
      g_pFrameBuffer[1] = 0x3E;

      g_pFrameBuffer[3] = 0x3E;
      g_pFrameBuffer[4] = 0x3E;
      g_pFrameBuffer[5] = 0x3E;
      
      g_pFrameBuffer[8] = 0x3E;
    }
  }
  
  // Point to first frame
  g_CurrentFrameIndex = 0;
}

inline void ClearSerialReceiveBuffer()
{
  while (SerialToHost.available())
    SerialToHost.read();   // Read and drop bytes in RX buffer
}

inline void ReadSerialAndWriteToFrameBuffer()
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
}


//////////////////////////// Start here
void setup()
{
  // Initialize random seed generator
  randomSeed(analogRead(0));
  
  // Initialize SPI for controlling LEDs and Serial for communicating with host
  //SPI.begin();
  //SPI.endTransaction();
  
  SerialToHost.begin(SERIAL_SPEED_BPS);
  
  // Configure SPI Slave Select pins as output pins and deselected slaves in SPI
  for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
  {
    pinMode(LEDMATRIX_SELECT_PINS[i], OUTPUT);
    digitalWrite(LEDMATRIX_SELECT_PINS[i], HIGH);
  }
  
  // Fill default pattern for frame buffer
  fillFrameBufferWithDefaultPattern();
  
  // Set position of next write buffer
  g_NextFrameBufferWriteBytePos = (TOTAL_FRAME_BUFFER_SIZE - ONE_FRAME_SIZE);
  
  // Properly set reset command flag
  g_bResetNowCommand = false;
  
  // Notify host that this LED controller has been initialized
  delay(1000);
  ClearSerialReceiveBuffer();
  SerialToHost.println(F("INITIALIZED"));
  SerialToHost.flush();
}

void loop()
{
  SPI.beginTransaction(SPISettings(F_CPU, LSBFIRST, SPI_MODE0));
  
  // The following message is a hint for host to send the next frame
  SerialToHost.println(F("SYNC"));
  SerialToHost.flush();
  
  // Draw current frame
  // NOTE: We need to rapidly redraw each frame multiple times
  // as we can only turn ON one row of a LED at a time.
  #ifdef PRINT_MILLIS_PER_FRAME
  unsigned long start_time = millis();
  #endif
  
  for (uint8_t t = 0; t < NUM_REDRAW_EACH_FRAME; ++t)
  {
    for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
    {
      byte *pCurrentMatrixFrameBuffer = &g_pFrameBuffer[(g_CurrentFrameIndex * ONE_FRAME_SIZE) + 
                                                        (i * ONE_MATRIX_FRAME_SIZE)];
      for (uint8_t j = 0; j < NUM_ROWS_PER_MATRIX; ++j)
      {
        digitalWrite(LEDMATRIX_SELECT_PINS[i], LOW);  // Select a slave LED matrix
        for (uint8_t k = 0; k < NUM_COLORS_PER_ROW_DOT; ++k)
        {
          SPI.transfer(pCurrentMatrixFrameBuffer[j * NUM_COLORS_PER_ROW_DOT + k]);
        }
        SPI.transfer(0x80 >> j);  // Send row index for current LED matrix

        digitalWrite(LEDMATRIX_SELECT_PINS[i], HIGH); // Deselect the selected LED matrix
      }
      
      // Explicitly need to turn off the last row of LEDs in the matrix
      // before displaying next frame so that unwanted lingering previous
      // data for last row does not remain.
      digitalWrite(LEDMATRIX_SELECT_PINS[i], LOW);
      for (uint8_t k = 0; k < NUM_COLORS_PER_ROW_DOT; ++k)
      {
        SPI.transfer(LED_ROW_OFF);
      }
      SPI.transfer(0x01 << (NUM_ROWS_PER_MATRIX - 1));
      digitalWrite(LEDMATRIX_SELECT_PINS[i], HIGH);
    }
    
    // If host has sent us frame data, we write it to frame buffer data
    ReadSerialAndWriteToFrameBuffer();
  }
  
  #ifdef PRINT_MILLIS_PER_FRAME
  sprintf_P(g_pStringBuffer, (PGM_P)F("INFO: 1 frame took %i ms."), (millis() - start_time));
  SerialToHost.println(g_pStringBuffer);
  #endif
  
  // Increment current frame index pointer
  g_CurrentFrameIndex = (g_CurrentFrameIndex + 1) % TOTAL_FRAMES;

  SPI.endTransaction();
}
