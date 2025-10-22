#ifndef __DtIoctl_h__
#define __DtIoctl_h__

#include "oldacfg.h"
#include "olerrors.h"


// This is defined in XP version of the Windows DDK header file usb.h
#ifndef USBD_STATUS_XACT_ERROR
#define USBD_STATUS_XACT_ERROR 0xc0000011
#endif

// The following IOCTL codes use BUFFERED_IO.
// This means that in kernel mode the data is read/written to the system buffer.
// and in user mode, the DeviceIoControl behaves as follows:
//
// lpInBuffer: OLWDM_API packet sent to driver
// nInBufferSize: sizeof(OLWDM_API)
// lpOutBuffer: OLWDM_API packet returned from driver   
// nOutputBufferSize: size of (OLWDM_API).  
// lpBytesReturned: actual number of bytes read

#define DTOL_IRP_MN_BUF_BASE  0x900

// NOTE: following IOCTLs and associated codes have been retired:
// DTOL_IRP_MN_OPEN, DTOL_IRP_MN_BUF_BASE + 0
// DTOL_IRP_MN_CLOSE, DTOL_IRP_MN_BUF_BASE + 1
// DTOL_IRP_MN_BURSTDTCONNECT, DTOL_IRP_MN_BUF_BASE + 12

#define DTOL_IRP_MN_READEVENTS \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 2), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_SETSINGLEVALUE \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 3), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_GETSINGLEVALUE \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 4), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_CONFIG \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 5), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_START \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 6), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_STOP \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 7), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_PAUSE \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 8), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_CONTINUE \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 9), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_RESET \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 10), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_ABORT \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 11), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_PRESTART \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 13), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_SIMULSTART \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 14), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_WRITEREG \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 15), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_READREG \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 16), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_SET_HW_INFO \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 17), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_GET_HW_INFO \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 18), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define  DTOL_IRP_MN_PEND_DRIVER_EVENT_HOOK \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 19), METHOD_BUFFERED, FILE_ANY_ACCESS )


// The following IOCTL uses DIRECT_IO.
// This means that in kernel mode the data is read/written to MDL descriptors mapped from the Irp.
// and in user mode, the DeviceIoControl behaves as follows:

// ( NOTE: Don't be misled by the DeviceIoControl Params named OutBuffer and InBuffer, Buffer A & B
//   would have been a better naming scheme...InBuffer ( Buffer A ) is used to pass in the context
//   for the IOCTL ( i.e susbsystem & element ) while OutBuffer ( Buffer B ) is used to pass the actual
//   Read or Write data in either direction.  OutBuffer is in fact bi-directional when using DIRECT_IO.

// Perform an IN data transfer for the specified subsystem & element.

// lpInBuffer: OLWDM_API packet sent to driver ( specifies subsystem and element for Read ) 
// nInBufferSize: sizeof(OLWDM_API)
// lpOutBuffer: Buffer to hold data read from the device.  
// nOutputBufferSize: size of lpOutBuffer.  This parameter determines the size of the data transfer.
// lpBytesReturned: actual number of bytes read
// 
#define DTOL_IRP_MN_FLUSHINPROCESS \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 20), METHOD_OUT_DIRECT, FILE_ANY_ACCESS )


#define DTOL_IRP_MN_WAIT_FOR_COMPLETE \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 21), METHOD_BUFFERED, FILE_ANY_ACCESS )

// This IOCTL is used with the DT9841 DSP board
#define DTOL_IRP_MN_COMM_IOCTL \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 22), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_READBUF_IOCTL \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 23), METHOD_OUT_DIRECT, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_WRITEBUF_IOCTL \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 24), METHOD_OUT_DIRECT, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_WRITE_CAL_POT \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 25), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_READ_CAL_POT \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 26), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_GETSINGLEVALUES \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 27), METHOD_BUFFERED, FILE_ANY_ACCESS )
    
#define DTOL_IRP_MN_IEPECONFIG	 \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 28), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_GETSINGLEFLOAT \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 29), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_GETSINGLEFLOATS \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 30), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_GETCJCTEMPERATURE \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 31), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_GETCJCTEMPERATURES \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 32), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_CONFIG_THERMCOUPLES \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 33), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_SETSINGLEVALUES \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 34), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_AUTO_CALIBRATE \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 35), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_WRITEMEM \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 36), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_READMEM \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 37), METHOD_BUFFERED, FILE_ANY_ACCESS )

// These commands are used to read and write hardware parameters - an example would be 
// default settings stored in EEPROM (if applicable) set via the Control Panel.
#define DTOL_IRP_MN_READ_HW_PARAM \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 38), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_WRITE_HW_PARAM \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 39), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_MUTE \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 40), METHOD_BUFFERED, FILE_ANY_ACCESS )

#define DTOL_IRP_MN_UNMUTE \
    CTL_CODE( FILE_DEVICE_UNKNOWN, (DTOL_IRP_MN_BUF_BASE + 41), METHOD_BUFFERED, FILE_ANY_ACCESS )


// HW_PARAM_INFO
//
// Use this structure when processing the following commands:
//		DTOL_IRP_MN_READ_HW_PARAM
//		DTOL_IRP_MN_WRITE_HW_PARAM
//
// These commands pass a HW_PARAM_INFO structure with a sub-command dependent number of 
// additional bytes. A byte count field indicates the number of additional bytes.

// Subcommand. Associated data listed below.
typedef enum
{
	HW_COUPLING = 0,		// AC/DC coupling (read/write).
	HW_CURRENT_SOURCE,	// current source (read/write)
	HW_POWER_SOURCE,		// Read the power source powering the device
	HW_STATE,
	HW_STRAIN_GAGE,
	HW_TEDS,
	HW_CJC_CAL_OFFSET,
	HW_INPUT_TERMINATION,
	HW_TIMESTAMPS
	// add more here as needed
} HW_PARAM_TYPE;

// HW_COUPLING
//		Read:	Each byte that follows contains an 8 bit integer for that ADC channel for the
//				element/subsystem (0-255)
//				Output contains 1 byte per ADC that was read of type (BYTE)COUPLING_TYPE
//		Write:	Each 2 bytes that follow has 
//					one byte with the ADC number and 
//					one byte for its value of type (BYTE)COUPLING_TYPE

// HW_CURRENT_SOURCE
//		Read:	Each byte that follows contains an 8 bit integer for that ADC channel for the
//				corresponding element/subsystem (0-255)
//				Output contains 1 byte per ADC that was read of type (BYTE)EXCITATION_CURRENT_SRC
//		Write:	Each 2 bytes that follow has 
//					one byte with the ADC number and 
//					one byte for its value of type (BYTE)EXCITATION_CURRENT_SRC

// HW_STATE
//		Read:	4 bytes that follows contains a DWORD integer corresponding to SUB_STATES enumeration
//				
//		Write: 4 bytes that follows contains a DWORD integer corresponding to SUB_STATES enumeration

// HW_STRAIN_GAGE
//		Write:	Two bytes follow for each physical channel. 
//				The first byte contains the bridge configuratio. 
//				The second byte contains the shunt calibration (boolean). 
//				These pair repeat until all channels have been accounted for.

// HW_CJC_CAL_OFFSET
//		Read:	The first byte that follows contains an 8 bit integer for the ADC channel for the
//					corresponding element/subsystem (0-255)
//				The second byte contains the "register" value - "0" is the current user setting
//					"1" is the factory setting, "2" is the current runtime setting (some devices
//					may use -1 for this field)
//				Output contains 4 bytes for the returned 'float' value.
//		Write:	The first bytes that follows contains an 8 bit integer for the ADC channel for the 
//					corresponding element/subsystem (0-255)
//				The second byte contains the "register" value - "0" is the current user setting
//					"1" is the factory setting, "2" is the current runtime setting (some devices
//					may use -1 for this field)
//				The 3rd through 6th bytes contains a CJC Cal Offset value of type 'float' (32 bits).

// This is the input to the DeviceIoControl read or write command
typedef struct
{
	OLSS				ssType;				// use if necessary
	UINT				ssElement;			// use if necessary
	HW_PARAM_TYPE		hwParam;			// the particular parameter to read or write (see enum)
	ULONG				ulDataByteCount;	// number of additional bytes that follow. Use 0 if command
											// has no data. Note sizeof(HW_PARAM_INFO) is min size for
											// input data to DeviceIoControl even if ulDataByteCount=0
	UCHAR				ucData[1];			// Bytes that follow. This is a placeholder for the first byte
											// even if not used. 
} HW_PARAM_INFO, *PHW_PARAM_INFO;

 
// READ_EVENTS_API
//
// Use this substructure for processing the following IOCTLs:
//
// DTOL_IRP_MN_READEVENTS
//
typedef struct
{
   ULONG         ulEvents;
}READ_EVENTS_INFO, *PREAD_EVENTS_INFO;


// SINGLE_VALUE_INFO
//
// Use this sub-structure for processing the following IOCTLs:
//
// DTOL_IRP_MN_SETSINGLEVALUE 
// DTOL_IRP_MN_GETSINGLEVALUE 
//
typedef struct
{
   ULONG          ulChannel;
   LONG           lValue;
   LARGE_INTEGER  liGain;
   BOOLEAN        bAutoRange;
} SINGLE_VALUE_INFO, *PSINGLE_VALUE_INFO;


// SINGLE_VALUES_INFO
//
// Use this sub-structure for processing the following IOCTLs:
//
// DTOL_IRP_MN_SETSINGLES VALUE 
// DTOL_IRP_MN_GETSINGLESVALUE 
//
typedef struct
{
   LARGE_INTEGER  liGain;
   LONG           lValues[1];	// First value, followed by n others
} SINGLE_VALUES_INFO, *PSINGLE_VALUES_INFO;


// SINGLE_FLOAT_INFO
//
// Use this sub-structure for processing the following IOCTLs:
//
// DTOL_IRP_MN_SETSINGLEFLOAT 
// DTOL_IRP_MN_GETSINGLEFLOAT 
//
typedef struct
{
   ULONG          ulChannel;
   FLOAT           fValue;
   LARGE_INTEGER  liGain;
} SINGLE_FLOAT_INFO, *PSINGLE_FLOAT_INFO;


// SINGLE_FLOATS_INFO
//
// Use this sub-structure for processing the following IOCTLs:
//
// DTOL_IRP_MN_SETSINGLEFLOATS 
// DTOL_IRP_MN_GETSINGLEFLOATS 
//
typedef struct
{
   LARGE_INTEGER  liGain;
   FLOAT          fValues[1];	// First value, followed by n others
} SINGLE_FLOATS_INFO, *PSINGLE_FLOATS_INFO;



//  CONFIGURATION_INFO
//
// Use this sub-structure for processing the following IOCTLs:
//
// DTOL_IRP_MN_CONFIG
//
typedef struct
{
     DEVICE_CFG  cfgInfo;
} CONFIGURATION_INFO, *PCONFIGURATION_API;
 
#if defined(_WIN64)
typedef struct
{
     DEVICE_CFG32  cfgInfo32;
} CONFIGURATION_INFO32, *PCONFIGURATION_API32;
#endif

// REGISTER_INFO
//
// Use this sub-structure for processing the following IOCTLs:
//
// DTOL_IRP_MN_READREG
// DTOL_IRP_MN_WRITEREG
//
typedef struct
{
   ULONG         ulOffset;
   ULONG         ulData;
   ULONG         ulSize;
} REGISTER_INFO, *PREGISTER_INFO;


// MEMORY_INFO
//
// Use this sub-structure for processing the following IOCTLs:
//
// DTOL_IRP_MN_READMEM
// DTOL_IRP_MN_WRITEMEM
//
typedef struct
{
   ULONG         ulAddress;
   BYTE          *pData;
   ULONG         ulNumBytes;
} MEMORY_INFO, *PMEMORY_INFO;


// HARDWARE_INFO
//
// Use this sub-structure for processing the following IOCTLs:
//
// DTOL_IRP_MN_SET_HW_INFO
// DTOL_IRP_MN_GET_HW_INFO
//
typedef struct
{
     DTBUS_TYPE  DtBusType;
     WORD        VendorId; 
     WORD        DeviceId; 
     WORD        ProductId; 
     ULONG       SerialNumber;
     ULONG       Reserved;
     DRIVER_SPECIFIC_INFO DriverSpecificInfo;
} HARDWARE_INFO, *PHARDWARE_INFO;
 

// CAL_POT_INFO
//
// Use this sub-structure for processing the following IOCTLs:
//
// DTOL_IRP_MN_READ_CAL_POT
// DTOL_IRP_MN_WRITE_CAL_POT
//
typedef struct
{
   ULONG         ulChipNum;
   ULONG         ulPotNum;
   ULONG         ulRegNum;
   ULONG         ulData;
} CAL_POT_INFO, *PCAL_POT_INFO;



// Messages used in DRIVER_MESSAGE_INFO packet
// Use MSBit to indicate messages which indicate an error condition
// Some correlation to Windows Open Layers messages in many cases.
#define  DATA_READY      0

#define  DT_DATA_OVERRUN            0x80000001    // AD, DI  
#define  DT_DATA_UNDERRUN           0x80000002    // DA, DO
#define  DT_GENERAL_FAILURE         0x80000003    // System call failed
#define  DT_TRIGGER_ERROR           0x80000004    // A Trigger Error Occurred...

#define  DT_DEVICE_REMOVAL          0x00000003
#define  DT_PRE_TRIGGER_DATA_DONE   0x00000004
#define  DT_EVENT_DONE              0x00000005
#define  DT_BUFFER_REUSED           0x00000006
#define  DT_EVENT_DONE_WITH_DATA    0x00000007
#define  DT_IO_COMPLETE             0x00000008
#define  DT_MESSAGE_RCVD            0x00000009
#define  DT_STATUS_XACT_ERROR       0x0000000A
#define  DT_START_TRIGGER_DETECTED	0x0000000B
#define  DT_REFERENCE_TRIGGER_DETECTED	0x0000000C




typedef enum
{
	NORMAL = 0,
	OVER_CLOCKED = 1,
	USB_ERROR = 2
} ERROR_TYPES;

// DRIVER_MESSAGE_INFO
//
// Use this sub-structure for processing the following IOCTLs:
//
// DTOL_IRP_MN_PEND_DRIVER_EVENT_HOOK 
//
typedef struct
{
   ULONG         ulDriverMessage;
   ULONG         ulDriverMessageData;
} DRIVER_MESSAGE_INFO, *PDRIVER_MESSAGE_INFO;






// And No substructures are required for the following IOCTLs:
//
//
// DTOL_IRP_MN_START
// DTOL_IRP_MN_STOP
// DTOL_IRP_MN_PAUSE
// DTOL_IRP_MN_CONTINUE
// DTOL_IRP_MN_RESET
// DTOL_IRP_MN_ABORT
// DTOL_IRP_MN_BURSTDTCONNECT
// DTOL_IRP_MN_PRESTART
// DTOL_IRP_MN_SIMULSTART
// DTOL_IRP_MN_READ
// DTOL_IRP_MN_WRITE

// OLWDM_API
//
typedef struct
{
   OLSS        ssType;
   UINT        ssElement;
   SS_STATES   ssState;
   OLSTATUS    ssErrStatus;
 
   union
   { 
      READ_EVENTS_INFO     ReadEventsInfo;
      SINGLE_VALUE_INFO    SingleValueInfo;
      SINGLE_VALUES_INFO   SingleValuesInfo;
      CONFIGURATION_INFO   ConfigInfo;
      REGISTER_INFO        RegisterInfo; 
      MEMORY_INFO          MemoryInfo; 
      HARDWARE_INFO        HardwareInfo;
      DRIVER_MESSAGE_INFO  DriverMessageInfo;
	  CAL_POT_INFO         CalPotInfo;
      SINGLE_FLOAT_INFO    SingleFloatInfo;
      SINGLE_FLOATS_INFO   SingleFloatsInfo;
   } u;

} OLWDM_API, *POLWDM_API;


#if _WDM_

#define COMPLETE_IRP(I, status)     I.PnpComplete(this, status)
#define NEXT_IRP(I)                 PnpNextIrp(I)

#else

#define COMPLETE_IRP(I, status)     I.Complete(status)
#define NEXT_IRP(I)                 NextIrp(I)

#endif // _WDM_


//
// Define the OLWDM_API structure for Win64 (thunking).
//
#if defined(_WIN64)
typedef struct 
{
     OLSS        ssType;
   UINT        ssElement;
   SS_STATES   ssState;
   OLSTATUS    ssErrStatus;
 
   union
   { 
      READ_EVENTS_INFO     ReadEventsInfo;
      SINGLE_VALUE_INFO    SingleValueInfo;
      SINGLE_VALUES_INFO   SingleValuesInfo;
      CONFIGURATION_INFO32   ConfigInfo;
      REGISTER_INFO        RegisterInfo; 
      MEMORY_INFO          MemoryInfo; 
      HARDWARE_INFO        HardwareInfo;
      DRIVER_MESSAGE_INFO  DriverMessageInfo;
	   CAL_POT_INFO         CalPotInfo;
      SINGLE_FLOAT_INFO    SingleFloatInfo;
      SINGLE_FLOATS_INFO   SingleFloatsInfo;
   } u;
}OLWDM_API32, *POLWDM_API32;

#endif


#endif // __DtIoctl_h__

