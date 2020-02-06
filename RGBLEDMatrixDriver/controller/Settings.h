// SETTINGS
//#define PRINT_MILLIS_PER_FRAME      // NOTE: Uncomment this line to print milliseconds that a frame is shown to serial

#define LED_ROW_ON                            (byte)0x00    // NOTE: This is valid for EP-005 LED matrix
#define LED_ROW_OFF                           (byte)0xFF    // NOTE: This is valid for EP-005 LED matrix
#define LED_ROW_ALTERNATE_ON                  (byte)0xAA    // NOTE: This is valid for EP-005 LED matrix
#define SERIAL_SPEED_BPS                      57600		      // CAUTION: Some chips may not support this baud rate
#define RESET_COMMAND                         "RESET\r\n"
#define RESET_COMMAND_SIZE                    7
#define NUM_LED_MATRICES                      4
#define NUM_ROWS_PER_MATRIX                   8
#define NUM_COLORS_PER_ROW_DOT                3
#define ONE_MATRIX_FRAME_SIZE                 (NUM_ROWS_PER_MATRIX * NUM_COLORS_PER_ROW_DOT)
#define ONE_FRAME_SIZE                        (NUM_LED_MATRICES * ONE_MATRIX_FRAME_SIZE)
#define TOTAL_FRAMES                          12
#define TOTAL_FRAME_BUFFER_SIZE               (TOTAL_FRAMES * ONE_FRAME_SIZE)   // NOTE: For 4 matrices, this allows for 12 frames
#define NUM_REDRAW_EACH_FRAME                 118                     // NOTE: This value allows us to set milliseconds to show per frame
#define _LEDMATRIX_SELECT_PINS								{ 10, 11, 12, 13 }      // CAUTION: Make sure the number of pins match 'NUM_LED_MATRICES'
#define _SS_MAX_RX_BUFF                       128                     // CAUTION: Needs to be able to hold one frame and should be a power of 2
