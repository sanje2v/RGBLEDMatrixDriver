// OnHost.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include <iostream>
#include <Windows.h>

int main()
{
    HANDLE hComm;  // Handle to the Serial port
    BOOL   Status; // Status
    DCB dcbSerialParams = { 0 };  // Initializing DCB structure
    COMMTIMEOUTS timeouts = { 0 };  //Initializing timeouts structure
    const DWORD  dwInQueue = 1024;
    const DWORD  dwOutQueue = 1024;
    const DWORD dataSize = 255;// 768;
    char SerialBuffer[dataSize]; //Buffer to send and receive data
    DWORD BytesWritten = 0;          // No of bytes written to the port
    DWORD dwEventMask;     // Event mask to trigger
    char  ReadData;        // Temporary Character
    DWORD NoBytesRead;     // Bytes read by ReadFile()
    int loop = 0;
    wchar_t pszPortName[10] = { 0 }; //com port id
    wchar_t PortNo[20] = { 0 }; //contain friendly name

    for (char i = 0; i < dataSize; ++i)
        SerialBuffer[i] = i;

    //Enter the com port id
    //printf_s("Enter the COM Port: ");
    //wscanf_s(L"%s", pszPortName, (unsigned)_countof(pszPortName));
    //swprintf_s(PortNo, 20, L"\\\\.\\%s", pszPortName);
    swprintf_s(PortNo, 20, L"\\\\.\\COM5");

    //Open the serial com port
    hComm = CreateFile(PortNo, //friendly name
        GENERIC_READ | GENERIC_WRITE,      // Read/Write Access
        0,                                 // No Sharing, ports cant be shared
        NULL,                              // No Security
        OPEN_EXISTING,                     // Open existing port only
        0,                                 // Non Overlapped I/O
        NULL);                             // Null for Comm Devices
    if (hComm == INVALID_HANDLE_VALUE)
    {
        printf_s("\n Port can't be opened\n\n");
        return -1;
    }
    
    if (SetupComm(hComm, dwInQueue, dwOutQueue) == FALSE)
    {
        printf_s("\n Couldn't set RX and TX buffer sizes\n\n");
        goto Exit1;
    }

    //Setting the Parameters for the SerialPort
    dcbSerialParams.DCBlength = sizeof(dcbSerialParams);
    Status = GetCommState(hComm, &dcbSerialParams); //retreives  the current settings
    if (Status == FALSE)
    {
        printf_s("\nError to Get the Com state\n\n");
        goto Exit1;
    }

    dcbSerialParams.BaudRate = CBR_115200;      //BaudRate = 256000
    dcbSerialParams.ByteSize = 8;             //ByteSize = 8
    dcbSerialParams.StopBits = ONESTOPBIT;    //StopBits = 1
    dcbSerialParams.Parity = NOPARITY;      //Parity = None
    //dcbSerialParams.fAbortOnError = TRUE;
    Status = SetCommState(hComm, &dcbSerialParams);
    if (Status == FALSE)
    {
        printf_s("\nError to Setting DCB Structure\n\n");
        goto Exit1;
    }

    //Setting Timeouts
    /*timeouts.ReadIntervalTimeout = 50;
    timeouts.ReadTotalTimeoutConstant = 50;
    timeouts.ReadTotalTimeoutMultiplier = 10;
    timeouts.WriteTotalTimeoutConstant = 50;
    timeouts.WriteTotalTimeoutMultiplier = 10;

    if (SetCommTimeouts(hComm, &timeouts) == FALSE)
    {
        printf_s("\nError to Setting Time outs");
        goto Exit1;
    }*/

    // Purge all data
    if (PurgeComm(hComm, PURGE_RXABORT | PURGE_RXCLEAR | PURGE_TXABORT | PURGE_TXCLEAR) == FALSE)
    {
        printf_s("\nFailed to purge buffers.\n\n");
        goto Exit1;
    }

    for (int i = 0; i < 10000; ++i)
    {
        loop = 0;

        //Writing data to Serial Port
        Status = WriteFile(hComm,// Handle to the Serialport
            SerialBuffer,            // Data to be written to the port
            sizeof(SerialBuffer),   // No of bytes to write into the port
            &BytesWritten,  // No of bytes written to the port
            NULL);
        if (Status == FALSE && BytesWritten != sizeof(SerialBuffer))
        {
            printf_s("\nFail to write");
            goto Exit1;
        }

        //print numbers of byte written to the serial port
        printf_s("\nNumber of bytes written to the serial port = %d\n\n", BytesWritten);

        //Setting Receive Mask
        Status = SetCommMask(hComm, EV_RXCHAR);
        if (Status == FALSE)
        {
            printf_s("\nError to in Setting CommMask\n\n");
            goto Exit1;
        }

        //Setting WaitComm() Event
        Status = WaitCommEvent(hComm, &dwEventMask, NULL); //Wait for the character to be received
        if (Status == FALSE)
        {
            printf_s("\nError! in Setting WaitCommEvent()\n\n");
            goto Exit1;
        }

        //Read data and compare echo with buffer
        do
        {
            Status = ReadFile(hComm, &ReadData, sizeof(ReadData), &NoBytesRead, NULL);
            if (Status != FALSE)
            {
                //printf_s("%d", ReadData);
                if (SerialBuffer[loop] != ReadData)
                {
                    printf_s("ERROR: Unmatching byte at index: %d which was %d instead of %d\n\n", loop, ReadData, SerialBuffer[loop]);
                    goto Exit1;
                }
                ++loop;
            }
        } while (loop < dataSize);
        //--loop; //Get Actual length of received data
        printf_s("\nNumber of bytes received and checked = %d\n\n", loop);
        //print receive data on console
        printf_s("\n\n");
    }

    Exit1:
        CloseHandle(hComm);//Closing the Serial Port

    //system("pause");
    
    return 0;
}

// Run program: Ctrl + F5 or Debug > Start Without Debugging menu
// Debug program: F5 or Debug > Start Debugging menu

// Tips for Getting Started: 
//   1. Use the Solution Explorer window to add/manage files
//   2. Use the Team Explorer window to connect to source control
//   3. Use the Output window to see build output and other messages
//   4. Use the Error List window to view errors
//   5. Go to Project > Add New Item to create new code files, or Project > Add Existing Item to add existing code files to the project
//   6. In the future, to open this project again, go to File > Open > Project and select the .sln file
