#if !defined(_DISPATCH_)
#define _DISPATCH_

class CDtDataCopyThread;

#include <oldacfg.h>
#include <TedsApi.h>
#include <rtdcoeffs.h>
#include <ChannelList.h>


#define OLDRV_GETSSCAPS                (DRV_USER+0)
#define OLDRV_SETDMAUSAGE              (DRV_USER+1)
#define OLDRV_GETDMAUSAGE              (DRV_USER+2)
#define OLDRV_SETTRIGGEREDSCANUSAGE    (DRV_USER+3)
#define OLDRV_GETTRIGGEREDSCANUSAGE    (DRV_USER+4)
#define OLDRV_SETCHANNELLISTSIZE       (DRV_USER+5)
#define OLDRV_GETCHANNELLISTSIZE       (DRV_USER+6)
#define OLDRV_SETCHANNELLISTENTRY      (DRV_USER+7)
#define OLDRV_GETCHANNELLISTENTRY      (DRV_USER+8)
#define OLDRV_SETGAINLISTENTRY         (DRV_USER+9)
#define OLDRV_GETGAINLISTENTRY         (DRV_USER+10)
#define OLDRV_SETCHANNELFILTER         (DRV_USER+11)
#define OLDRV_GETCHANNELFILTER         (DRV_USER+12)
#define OLDRV_SETRANGE                 (DRV_USER+13)
#define OLDRV_GETRANGE                 (DRV_USER+14)
#define OLDRV_SETCHANNELTYPE           (DRV_USER+15)
#define OLDRV_GETCHANNELTYPE           (DRV_USER+16)
#define OLDRV_SETENCODING              (DRV_USER+17)
#define OLDRV_GETENCODING              (DRV_USER+18)
#define OLDRV_SETTRIGGER               (DRV_USER+19)
#define OLDRV_GETTRIGGER               (DRV_USER+20)
#define OLDRV_SETRESOLUTION            (DRV_USER+21)
#define OLDRV_GETRESOLUTION            (DRV_USER+22)
#define OLDRV_SETCLOCKSOURCE           (DRV_USER+23)
#define OLDRV_GETCLOCKSOURCE           (DRV_USER+24)
#define OLDRV_SETCLOCKFREQUENCY        (DRV_USER+25)
#define OLDRV_GETCLOCKFREQUENCY        (DRV_USER+26)
#define OLDRV_SETRETRIGGERFREQUENCY    (DRV_USER+27)
#define OLDRV_GETRETRIGGERFREQUENCY    (DRV_USER+28)
#define OLDRV_SETEXTERNCLOCKDIVIDER    (DRV_USER+29)
#define OLDRV_GETEXTERNCLOCKDIVIDER    (DRV_USER+30)
#define OLDRV_SETGATETYPE              (DRV_USER+31)
#define OLDRV_GETGATETYPE              (DRV_USER+32)
#define OLDRV_SETPULSETYPE             (DRV_USER+33)
#define OLDRV_GETPULSETYPE             (DRV_USER+34)
#define OLDRV_SETPULSEWIDTH            (DRV_USER+35)
#define OLDRV_GETPULSEWIDTH            (DRV_USER+36)
#define OLDRV_SETCOUNTERMODE           (DRV_USER+37)
#define OLDRV_GETCOUNTERMODE           (DRV_USER+38)
#define OLDRV_SETCASCADEMODE           (DRV_USER+39)
#define OLDRV_GETCASCADEMODE           (DRV_USER+40)
#define OLDRV_SETWRAPMODE              (DRV_USER+41)
#define OLDRV_GETWRAPMODE              (DRV_USER+42)
#define OLDRV_SETDATAFLOW              (DRV_USER+43)
#define OLDRV_GETDATAFLOW              (DRV_USER+44)
#define OLDRV_SETWINDOWHANDLE          (DRV_USER+45)
#define OLDRV_GETWINDOWHANDLE          (DRV_USER+46)
#define OLDRV_SETNOTIFYPROC            (DRV_USER+47)
#define OLDRV_GETNOTIFYPROC            (DRV_USER+48)
#define OLDRV_SETCHANNELLISTINHIBIT    (DRV_USER+49)
#define OLDRV_GETCHANNELLISTINHIBIT    (DRV_USER+50)
#define OLDRV_SETDIGITALIOLISTENTRY    (DRV_USER+51) 
#define OLDRV_GETDIGITALIOLISTENTRY    (DRV_USER+52) 
#define OLDRV_SETSYNCHRONOUSDIOUSAGE   (DRV_USER+53) 
#define OLDRV_GETSYNCHRONOUSDIOUSAGE   (DRV_USER+54) 
#define OLDRV_SETTRANSFERSIZE          (DRV_USER+55) 
#define OLDRV_GETTRANSFERSIZE          (DRV_USER+56) 
#define OLDRV_SETTRANSFERCOUNT         (DRV_USER+57) 
#define OLDRV_GETTRANSFERCOUNT         (DRV_USER+58) 
#define OLDRV_SETCHANNELRANGE          (DRV_USER+59)
#define OLDRV_GETCHANNELRANGE          (DRV_USER+60)
#define OLDRV_PUTBUFFER                (DRV_USER+61)
#define OLDRV_GETBUFFER                (DRV_USER+62)
#define OLDRV_GETQUEUESIZES            (DRV_USER+63)
#define OLDRV_FLUSHBUFFERS             (DRV_USER+64)
#define OLDRV_SETRETRIGGERMODE         (DRV_USER+65)
#define OLDRV_GETRETRIGGERMODE         (DRV_USER+66)

//  new for v2.5 
#define OLDRV_SETPRETRIGGERSOURCE       (DRV_USER+67)
#define OLDRV_GETPRETRIGGERSOURCE       (DRV_USER+68)
#define OLDRV_SETMULTISCANCOUNT         (DRV_USER+69)
#define OLDRV_GETMULTISCANCOUNT         (DRV_USER+70)

#define OLDRV_SETRETRIGGERSOURCE        (DRV_USER+71)
#define OLDRV_GETRETRIGGERSOURCE        (DRV_USER+72)

#define OLDRV_SETSPECIALVPICONFIGMODE   (DRV_USER+73)
#define OLDRV_GETSPECIALVPICONFIGMODE   (DRV_USER+74)

#define OLDRV_SETSTARTEDGE				(DRV_USER+75)
#define OLDRV_GETSTARTEDGE				(DRV_USER+76)
#define OLDRV_SETSTOPEDGE				(DRV_USER+77)
#define OLDRV_GETSTOPEDGE				(DRV_USER+78)
#define OLDRV_SETQUADRATURE             (DRV_USER+79)
#define OLDRV_SETCOUPLINGTYPE			(DRV_USER+80)
#define OLDRV_GETCOUPLINGTYPE			(DRV_USER+81)
#define OLDRV_SETIEPECURRENTSOURCE		(DRV_USER+82)
#define OLDRV_GETIEPECURRENTSOURCE		(DRV_USER+83)
#define OLDRV_SETIEPECURRENTVALUE		(DRV_USER+84)
#define OLDRV_GETIEPECURRENTVALUE		(DRV_USER+85)
#define OLDRV_GETCHANMAP				(DRV_USER+86)
#define OLDRV_ISRUNNING					(DRV_USER+87)
#define OLDRV_SET_THERMOCOUPLE_TYPE		(DRV_USER+88)	
#define OLDRV_GET_THERMOCOUPLE_TYPE		(DRV_USER+89)
#define OLDRV_SET_RETURN_CJC_TEMPERATURE_IN_STREAM	(DRV_USER+90)
#define OLDRV_GET_RETURN_CJC_TEMPERATURE_IN_STREAM	(DRV_USER+91)
#define OLDRV_SET_RTD_TYPE				(DRV_USER+92)	
#define OLDRV_GET_RTD_TYPE				(DRV_USER+93)
#define OLDRV_SET_SYNC_MODE				(DRV_USER+94)
#define OLDRV_GET_SYNC_MODE				(DRV_USER+95)
#define OLDRV_SET_FILTER_TYPE			(DRV_USER+96)
#define OLDRV_GET_FILTER_TYPE			(DRV_USER+97)
#define OLDRV_SET_CHAN_VOLTAGE_RANGE	(DRV_USER+98)	
#define OLDRV_GET_CHAN_VOLTAGE_RANGE	(DRV_USER+99)

#define OLDRV_SET_STALE_DATAFLAG_ENABLED	(DRV_USER+100)
#define OLDRV_GET_STALE_DATAFLAG_ENABLED	(DRV_USER+101)
#define OLDRV_GETDEVCAPS						(DRV_USER+102)
#define OLDRV_SET_TRIGGER_LEVEL				(DRV_USER+103)
#define OLDRV_GET_TRIGGER_LEVEL				(DRV_USER+104)
#define OLDRV_SET_TRIGGER_CHANNEL			(DRV_USER+105)
#define OLDRV_GET_TRIGGER_CHANNEL			(DRV_USER+106)
#define OLDRV_SET_POST_TRIGGER_SCANCOUNT	(DRV_USER+107)
#define OLDRV_GET_POST_TRIGGER_SCANCOUNT	(DRV_USER+108)
#define OLDRV_SET_REFERENCE_TRIGGER				(DRV_USER+109)
#define OLDRV_GET_REFERENCE_TRIGGER				(DRV_USER+110)

#define OLDRV_SET_STRAIN_EXCITATION_VOLTAGE_SOURCE	(DRV_USER+111)
#define OLDRV_GET_STRAIN_EXCITATION_VOLTAGE_SOURCE	(DRV_USER+112)
#define OLDRV_SET_STRAIN_EXCITATION_VOLTAGE			(DRV_USER+113)
#define OLDRV_GET_STRAIN_EXCITATION_VOLTAGE			(DRV_USER+114)
#define OLDRV_SET_STRAIN_BRIDGE_CONFIGURATION		(DRV_USER+115)
#define OLDRV_GET_STRAIN_BRIDGE_CONFIGURATION		(DRV_USER+116)
#define OLDRV_SET_STRAIN_SHUNT_RESISTOR				(DRV_USER+117)
#define OLDRV_GET_STRAIN_SHUNT_RESISTOR				(DRV_USER+118)
#define OLDRV_CONFIG_STRAIN							(DRV_USER+119)
#define OLDRV_GET_HARDWARE_TEDS						(DRV_USER+120)

#define OLDRV_SET_MULTISENSORTYPE		(DRV_USER+121)
#define OLDRV_GET_MULTISENSORTYPE		(DRV_USER+122)

#define OLDRV_SET_SENSOR_WIRING_CONFIGURATION		(DRV_USER+123)
#define OLDRV_GET_SENSOR_WIRING_CONFIGURATION		(DRV_USER+124)

#define OLDRV_SET_RTD_R0	(DRV_USER+125)
#define OLDRV_GET_RTD_R0	(DRV_USER+126)

#define OLDRV_SET_RTD_A		(DRV_USER+127)
#define OLDRV_GET_RTD_A		(DRV_USER+128)

#define OLDRV_SET_RTD_B		(DRV_USER+129)
#define OLDRV_GET_RTD_B		(DRV_USER+130)

#define OLDRV_SET_RTD_C		(DRV_USER+131)
#define OLDRV_GET_RTD_C		(DRV_USER+132)

#define OLDRV_SET_THERMISTOR_A		(DRV_USER+133)
#define OLDRV_GET_THERMISTOR_A		(DRV_USER+134)

#define OLDRV_SET_THERMISTOR_B		(DRV_USER+135)
#define OLDRV_GET_THERMISTOR_B		(DRV_USER+136)

#define OLDRV_SET_THERMISTOR_C		(DRV_USER+137)
#define OLDRV_GET_THERMISTOR_C		(DRV_USER+138)

#define OLDRV_SET_INPUT_TERMINATED_ENABLED	(DRV_USER+139)
#define OLDRV_GET_INPUT_TERMINATED_ENABLED	(DRV_USER+140)
#define OLDRV_GETCHANNELCAPS			(DRV_USER+141)	
#define OLDRV_GET_SUPPORTED_MULTISENSORTYPES (DRV_USER+142)
#define OLDRV_SET_BRIDGE_CONFIGURATION		(DRV_USER+143)
#define OLDRV_GET_BRIDGE_CONFIGURATION		(DRV_USER+144)


// NOTE - If you add any addition definitions in the list be sure to also
// add a corresponding string definition in the RC file


#define OLDRV_NULL                     (DRV_USER+149)
#define OLDRV_READEVENTS               (DRV_USER+150)
#define OLDRV_SETSINGLEVALUE           (DRV_USER+151)
#define OLDRV_GETSINGLEVALUE           (DRV_USER+152)
#define OLDRV_CONFIG                   (DRV_USER+153)
#define OLDRV_START                    (DRV_USER+154)
#define OLDRV_STOP                     (DRV_USER+155)
#define OLDRV_PAUSE                    (DRV_USER+156)
#define OLDRV_CONTINUE                 (DRV_USER+157)
#define OLDRV_RESET                    (DRV_USER+158)
#define OLDRV_ABORT                    (DRV_USER+159)
#define OLDRV_BURSTDTCONNECT           (DRV_USER+160)

#define OLDRV_PRESTART                 (DRV_USER+161)
#define OLDRV_SIMULSTART               (DRV_USER+162)
#define OLDRV_ALLOCATE                 (DRV_USER+163)
#define OLDRV_DEALLOCATE               (DRV_USER+164)
#define OLDRV_FLUSHINPROCESS           (DRV_USER+165)

#define OLDRV_WRITEREG                 (DRV_USER+166)
#define OLDRV_READREG                  (DRV_USER+167)

#define OLDRV_GETSINGLEVALUES          (DRV_USER+168)

#define OLDRV_IEPECONFIG               (DRV_USER+169)

#define OLDRV_GET_SINGLE_FLOAT			(DRV_USER+170)
#define OLDRV_GET_SINGLE_FLOATS			(DRV_USER+171)
#define OLDRV_GET_CJC_TEMPERATURE		(DRV_USER+172)
#define OLDRV_GET_CJC_TEMPERATURES		(DRV_USER+173)
#define OLDRV_SETSINGLEVALUES			(DRV_USER+174)
#define OLDRV_CONFIG_THERMCOUPLES		(DRV_USER+175)
#define OLDRV_AUTO_CALIBRATE			(DRV_USER+176)
#define OLDRV_MUTE						(DRV_USER+177)
#define OLDRV_UNMUTE					(DRV_USER+178)



// NOTE - If you add any addition definitions in the list be sure to also
// add a corresponding string definition in the RC file



#define OLDRVMSGMIN     (OLDRV_GETSSCAPS)
#define OLDRVMSGMAX     (OLDRV_GET_BRIDGE_CONFIGURATION)
#define OLDRVMSGCOUNT   (OLDRVMSGMAX - OLDRVMSGMIN + 1)

#define OLDRVUSERMIN    (OLDRV_READEVENTS)
#define OLDRVUSERMAX    (OLDRV_UNMUTE)
#define OLDRVUSERCOUNT  (OLDRVUSERMAX - OLDRVUSERMIN + 1)

typedef enum AcquisitionTriggerTypeEnum_tag
{
	AcquisitionTriggerTypeStart,
   AcquisitionTriggerTypeReference
}AcquisitionTriggerTypeEnum;



typedef struct 
{
    union 
    {
        struct 
        {                
            UINT  uiCap;
            UINT  uiIndex;
            DBL   dfCap;
        } Caps;                // GETSSCAPS
        
        UINT  uiDmaUse;         // SET/GETDMAUSAGE
        BOOL  fTrigUse;         // SET/GETTRIGGEREDSCANUSAGE
        UINT  uiChanListSize;   // SET/GETCHANNELLISTSIZE
        
        struct 
        {                
            UINT uiEntry;
            UINT uiChan;
        } ChannelListEntry;     // SET/GETCHANNELLISTENTRY
        
        struct 
        {          
            UINT uiEntry;
            DBL  dfGain;
        } GainListEntry;        // SET/GETGAINLISTENTRY
        
        struct 
        {    
            UINT  uiChannel;
            DBL   dfMin;
            DBL   dfMax;
        } Range;                // SET/GETRANGE, SET/GETCHANNELRANGE
        
        struct 
        {    
            UINT  uiChan;
            DBL   dfFreq;
        } ChannelFilter;        // SET/GETCHANNELFILTER
        
        UINT  uiChannelType;    // SET/GETCHANNELTYPE
        UINT  uiEncoding;       // SET/GETENCODING
        UINT  uiTrigger;        // SET/GETTRIGGER

        UINT  uiPreTrigger;     // SET/GETPRETRIGGER        SEB 12/27
        UINT  uiCount;          // SET/GETMULTISCANCOUNT    SEB 12/27
        
        UINT  uiReTrigger;      // SET/GETRETRIGGER         SEB 02/24
        
        UINT  uiResolution;     // SET/GETRESOLUTION
        UINT  uiClockSource;    // SET/GETCLOCKSOURCE
        DBL   dfFrequency;      // SET/GETCLOCKFREQUENCY ,SET/GETRETRIGGERFREQUENCY
        ULNG  ulDivider;        // SET/GETEXTERNCLOCKDIVIDER    
        UINT  uiGate;           // SET/GETGATETYPE
        UINT  uiPulse;          // SET/GETPULSETYPE
        UINT  uiPercent;        // SET/GETPULSEWIDTH
        UINT  uiMode;           // SET/GETCOUNTERMODE, SET/GETCASCADEMODE, GET/SETWRAPMODE
        ULNG  ulEvents;         // READEVENTS
		UINT  uiStartEdge;		// SET/GETSTARTEDGE
		UINT  uiStopEdge;		// SET/GETSTARTEDGE

        UINT  uiRetriggerMode;  // SET/GETRETRIGGERMODE     6/11/96  mak

        UINT uiElement;         //  olDaSimultaneousPrestart
        UINT OlSs;              //  olDaSimultaneousPrestart
        
        struct 
        {                  
            HWND   hWnd;
            WPARAM wParam;
            LPARAM lParam;
        } WindowNotification;   // SET/GETWINDOWHANDLE
        
        struct 
        {        
            UINT uiQueue;
            UINT uiSize;
        } QueueSize;            // GETQUEUESIZES
        
        UINT  uiFlow;           // SET/GETDATAFLOW
        HBUF  hBuf;             // SET/GETBUFFER
        struct 
        {             
            UINT  uiChannel;
            LNG   lValue;
            BOOL  bAutoRange;
            DBL   dfGain;
            DBL   dfValueVolts; 
        } SingleValue;          // SET/GETSINGLEVALUE

       struct 
        {             
            DBL   dfGain;
            LNG   lValues[MAX_NUM_DAC_CHANS];
        } SingleValues;         // SET/GETSINGLEVALUES

		struct 
        {             
            UINT  uiChannel;
            FLOAT fValue;
            DBL   dfGain;
        } SingleFloat;          // SET/GETSINGLEFLOAT

        struct 
        {             
            DBL   dfGain;
            FLOAT fValues[MAX_NUM_THERMOCOUPLES];
        } SingleFloats;         // SET/GETSINGLEFLOATS

        struct 
        {       
            UINT uiEntry;
            BOOL fInhibit;
        } InhibitEntry;         // SET/GETCHANNELLISTINHIBIT
        
        struct 
        {    
            UINT uiEntry;
            UINT uiValue;
        } IOListEntry;          // SET/GETDIGITALIOLISTENTRY
        
        BOOL fSyncDigitalIO;        // SET/GETSYNCHRONOUSDIOUSAGE
        BOOL bSpecialVpiConfigMode; // SET/GETSETSPECIALVPICONFIGMODE
        
        struct 
        {     
            HBUF  hBuf;
            ULNG  ulSamples;
        } FlushBuffer;          // FLUSHINPROCESS
        
        struct 
        {    
            OLNOTIFYPROC pfnFunc;
            WPARAM      wParam;
            LPARAM      lParam;
        } NotifyProc;           // SET/GETNOTIFYPROC

        struct
        {
            ULNG  ulData;           // Read/WriteReg            SEB 02/24
            ULNG  ulOffset;         // Read/WriteReg            SEB 02/24
            UINT  uiSize;           // Read/WriteReg            SEB 02/24
        } ReadWriteReg;         // Read/Write Register

		struct
		{
			 UINT ClockPreScale; 
			 BOOL X4Scaling;
			 UINT IndexMode;
		} SetQuad;
		
		struct 
        {    
            UINT  uiChannel;
            COUPLING_TYPE  eCouplingType;
        } Coupling;                // SET/GETCHANNELCOUPLING
        
        struct 
        {    
            UINT  uiChannel;
            EXCITATION_CURRENT_SRC eSource;
            DBL value;
        } IEPECurrent;                // SET/GETCHANNELCURRENT
        
        struct 
		{
			UINT	uiChanIndex;
			CHANNELMAP  ChanMap;
		} ChanMapInfo;

		BOOL  fIsRunning;         // IsRunning

        struct 
		{
			UINT	uiThermChan;
			UINT	uiThermType;
			BOOL	bWriteInfoToEPROM;
		} ThermInfo;

		struct 
		{
			UINT triggerType;
			AcquisitionTriggerTypeEnum acquisitionTriggerType;
			DBL	level;
			INT	channel;
			INT	scanCount;
		} TriggerInfo;

		BOOLEAN bReturnCjcTemperatureInStream;
		UINT  uiSyncMode;		// SET/GET Synchronization mode
		UINT  uiFilterType;
		BOOLEAN bStaleDataFlagEnabled;

		struct
		{
			UINT							uiChannel;
			STRAIN_EXCITATION_VOLTAGE_SRC	eStrainExcitationVoltageSource;
			DBL								StrainExcitationVoltage;
			STRAIN_GAGE_CONFIGURATION		eStrainConfiguration;
			BOOL							bStrainBridgeShuntEnabled;
		} StrainInfo;
		
		struct
		{
			UINT	uiChannel;
			TedsTemplateId	templateID;
			PVOID pTeds;
		} HardwareTedsInfo;

		struct
		{
			UINT							uiChannel;
			IO_TYPE						ioType;
			IO_TYPE						multiSensorType;
			SENSOR_WIRING_CONFIGURATION sensorWiringConfiguration;
			double RtdA;
			double RtdB;
			double RtdC;
			double RtdR0;
			UINT RTDType;
			double ThermistorA;
			double ThermistorB;
			double ThermistorC;

		} MultiSensorInfo;

		struct 
      {    
			UINT  uiChannel;
         BOOL value;
		} BooleanChannelInfo;
		struct 
      {    
			UINT  uiChannel;
         UINT value;
		} UintChannelInfo;
    };
}DISP_PKT;

typedef DISP_PKT *PDISP_PKT;
#define LPDISP_PKT PDISP_PKT

 
typedef struct personality_tag
   {
   // these guys are filled in pu the personality library
   // for the appropriate board and device
   PDBL     pdfGains;
   PDBL*    ppdfMinRanges;
   PDBL*    ppdfMaxRanges;
   PDBL     pdfFilters;
   PDBL     pdfResolutions;
   PUINT    puiCaps;
   PDBL     pdfCaps;
   }
PERSONALITY, *PPERSONALITY;

typedef struct SUBSYSTEM_CAPS_tag
   {
		bool    SupportsACCoupling;
		bool    SupportsDCCoupling;
		bool    SupportsInternCurrentSrc;
		bool    SupportsExternCurrentSrc;
		int		numCurrentValueItems;
		PDBL    pdCurrentValues;
		bool    SupportsWaveformModeOnly;
		bool	SupportsThermocouples;
		bool	SupportsTemperatureDataInStream;
		bool	InterleavedCJCInStream;
		bool	SupportsCjcSourceChannel;
		bool	SupportsCjcSourceInternal;
		double	CjcMillivoltsPerDegreeC;
		bool	ReturnsFloats;
		bool	CurrentOutputs;
		bool	SupportsPutSingleValues;
		bool	SupportsSvPosExternalTTLTrigger;
		bool	SupportsSvNegExternalTTLTrigger;
		bool	SupportsAutoCalibration;
		bool	SupportsRtds;
		bool	ReturnsOhms;
		bool    SupportsSynchronization;
		bool    SupportsThermFilters;
		bool    SupportsNoRawData;
		bool    SupportsVoltageRanges;
		bool	SupportsStaleDataFlag;
		bool	SupportsSoftwareReferenceTrigger;
		bool	SupportsPosExternalTTLReferenceTrigger;
		bool	SupportsNegExternalTTLReferenceTrigger;
		bool	SupportsPosThresholdReferenceTrigger;
		bool	SupportsNegThresholdReferenceTrigger;
		bool	SupportsPostReferenceTriggerScanCount;
		int		ThresholdStartTriggerSourcesCount;
		PINT	ThresholdStartTriggerSources;
		int		ThresholdReferenceTriggerSourcesCount;
		PINT	ThresholdReferenceTriggerSources;

		bool	SupportsStrainGage;
		bool	SupportsInternalExcitationVoltageSource;
		bool	SupportsExternalExcitationVoltageSource;
		double	MinExcitationVoltage;
		double	MaxExcitationVoltage;
		bool	SupportsShuntCalibration;
		bool	SupportsRemoteSense;
		bool	SupportsSyncBusReferenceTrigger;
		bool	SupportsMute;
		double DefaultFrequency;
		bool	SupportsThermocouple;
		bool	SupportsRTD;
		bool	SupportsResistance;
		bool	SupportsThermistor;
		bool SupportsMultiSensor;
		bool SupportsIepe;
		bool SupportsCurrent;
		bool SupportsBridgeBasedSensors;




// NOTE If you add any additional items here, you'll also need to make corresponding changes to
// the CapCommand enumeration (below)
   }
SUBSYSTEM_CAPS, *PSUBSYSTEM_CAPS;

typedef struct DEVICE_CAPS_tag
   {
		bool    SupportsInternalAndExternalPower;
   }
DEVICE_CAPS, *PDEVICE_CAPS;   

typedef struct tagIEPE_CAP
   {	
		int NumCouplingSupportChanCount;
		PUINT puiCouplingSupportChanList;

		int CurrentSupportChanCount;
		PUINT puiCurrentSupportChansList;

		int CurrentValsCount;
		PFLOAT pfCurrentValueList; // Current Source Value 4m,8m, etc.

		bool supExtCurrentSource;
		bool supInternalCurrentSource;
   }
IEPE_CAP, *PIEPE_CAP;



// located in personality module

#ifdef STRICT
typedef BOOL (WINAPI* BOARDINFOPROCEX)(UINT uiType, CHAR *szUserBoardName, PTSTR* ppszBoardName, PUINT* ppCounts);
#else
typedef FARPROC BOARDINFOPROCEX;
#endif

// name to use for GetProcAddress()
#ifdef _WIN64
#define BOARDINFOPROCNAMEEX  TEXT("BoardInfoProcEx")
#else
#define BOARDINFOPROCNAMEEX  TEXT("_BoardInfoProcEx@16")
#endif

// located in personality module

#ifdef STRICT
 typedef BOOL (WINAPI* PERSONALITYPROCEX)(UINT uiType, CHAR *szBoardName, OLSS ss, UINT el, PPERSONALITY pPersonality);
#else
 typedef FARPROC PERSONALITYPROCEX;
#endif

// name to use for GetProcAddress()
#ifdef _WIN64
#define PERSONALITYPROCNAMEEX  TEXT("PersonalityProcEx")
#else
#define PERSONALITYPROCNAMEEX  TEXT("_PersonalityProcEx@20")
#endif

/* 
  Provides a list of channel map items
*/
typedef struct _channelMapList
{
	int Count;				// Number of channel map items
	PCHANNELMAP pItems;		// A pointer to an array containing the <Count> items

} CHANNELMAP_LIST, *PCHANNELMAP_LIST;


/*
  Provides a list of per-channel strain information
*/
typedef struct _strainConfig
{
	STRAIN_GAGE_CONFIGURATION BridgeConfiguration;	// one of the supported bridge configs
	BOOL bShuntEnabled;								// "true" if shunt resistor is enabled
} STRAINCONFIG, *PSTRAINCONFIG;


typedef struct _strainConfigList
{
	int Count;				// Number of StrainInfo items
	STRAINCONFIG pItems[1];	// First of a list of identical structures
} STRAINCONFIG_LIST, *PSTRAINCONFIG_LIST;





// Capability commands
// These commands are passsed to the board's personality module.   If the perosnality module
// supports these commands it returns the appropraite value.  If the board does not support
// the feature it doesn't havce to implement the command and the property will be automatically
// be set to FALSE or 0.
typedef enum CapCommand_tag
{
		// For boards that allow switchable AC/DC coupling this should be TRUE
		bool_SupportsACCoupling = 0,

		// NOTE This should not be used by any code sinec old boards will not return TRUE for this
		// even though they all support DC coupling
		bool_SupportsDCCoupling,

		// Set to TRUE for IEPE boards (or others) that supports internal current sources
		bool_SupportsInternalCurrentSource,

		// Set to TRUE for IEPE boards (or others) that supports external current sources
		bool_SupportsExternalCurrentSource,

		// if bool_SupportsInternalCurrentSource==TRUE then this should return a list of 
		// supported current values in Amps
		double_GetCurrentValues,

		// Set to TRUE if the board supports thermocouple inputs.  There are two very
		// different types of thermcouple input boards.  If this property is TRUE then
		// you would then typically set all of the various properties below as a set.

		// DT9800 style board:
		//		bool_SupportsTemperatureDataInStream = FALSE
		//		bool_SupportsCjcSourceChannel = TRUE
		//		bool_SupportsCjcSourceInternal = FALSE
		//		intArray_CjcChannels = List of CJC chans (typically all 0's)
		//		bool_InterleavedCJCInStream = FALSE
		//		bool_ReturnsFloats = FALSE

		// DT9871 style board:
		//		bool_SupportsTemperatureDataInStream = TRUE
		//		bool_SupportsCjcSourceChannel = FALSE
		//		bool_SupportsCjcSourceInternal = TRUE
		//		intArray_CjcChannels = NOT USED
		//		bool_InterleavedCJCInStream = TRUE
		//		bool_ReturnsFloats = TRUE

		bool_SupportsThermocouples,

		// This only has meaning if bool_SupportsThermocouple=TRUE
		// Set to TRUE if board can return floating point temperature values (e.g DT9871).
		// If this is TRUE it also indicates that if the Therm Type is set to NONE the board 
		// will return floating point voltages.  If this is FALSE it indicates that the board
		// returns raw counts (e.g. DT9800) and its the job of the app (OL.WIN32) or OpenLayers 
		// (OL.NET) to convert to temperature.   If this property is FALSE, then the
		// intArray_CjcChannels (below) must alos be implemented.
		bool_SupportsTemperatureDataInStream,

		// This only has meaning if bool_SupportsTemperatureDataInStream = FALSE.  It indicates that
		// one of the A/D channel's is used as  the CJC input,n that
		// case, this array should contain an entry for each A/D channel that the boards supports.
		bool_SupportsCjcSourceChannel,

		// This only has meaning if bool_SupportsTemperatureDataInStream = TRUE.  It indicates that
		// the CJC is measured internally and does not use one of the standard user accessible
		// A/D channels.
		bool_SupportsCjcSourceInternal,

		// This array only has meaning if bool_SupportsCjcSourceChannel = TRUE.  In that
		// case, this array should contain an entry for each A/D channel that the boards supports.
		// Each entry specifies the A/D channel that contains the CJC data for that A/D channel.
		// SO for example on a DT9800 you would have 16 entries filled with 0 indicating that
		// all A/D channels should use A/D channel 0 as their CJC input.
		intArray_CjcChannels,

		// This only has meaning if bool_SupportsThermocouple=TRUE.  It contains the number of
		// millivolts per degree C of the CJC input
		double_CjcMillivoltsPerDegreeC,

		// This only applies to D/A subsystems.  If TRUE it indicates that the board does not 
		// support streaming but only supports Waveform mode (i.e download once and output 
		// continuously).  NOTE even if this is TRUE the DAC will also support single value output.
		// This is typically FALSE on most boards but its TRUE on the DT9837 DAC
		bool_SupportsWaveformModeOnly,

		// This only has meaning if bool_SupportsTemperatureDataInStream = TRUE.  It indicates that
		// the board can optionally interleave CJC data with A/D data (Voltage or temperature) in 
		// the data stream (e.g. DT9871).  
		bool_InterleavedCJCInStream,

		// TRUE indicates that the board returns data in floating point format (e.g. DT9871).
		// FALSE indicates that teh board returns data as integers.
		bool_ReturnsFloats,

		// TRUE indicates that the subsystem outputs current (ma).
		// FALSE indicates that the subsystem outputs voltage 
		bool_CurrentOutputs,

		// TRUE indicates that the subsystem supports olDaPutSingleValues()
		// FALSE indicates that the subsystem does NOT support olDaPutSingleValues()
		bool_SupportsPutSingleValues,
		
		// TRUE indicates that the subsystem supports Positive TTL External Trigger for SingleValue operations
		// FALSE otherwise 
		bool_SupportsSvPosExternalTrigger,
		
		// TRUE indicates that the subsystem supports Negative TTL External Trigger for SingleValue operations
		// FALSE otherwise 
		bool_SupportsSvNegExternalTrigger,

		// TRUE indicates that the subsystem supports internal auto calibration
		bool_SupportsAutoCalibration,

		// TRUE indicates that the subsystem supports RTDs
		bool_SupportsRtds,

		// TRUE indicates that the board returns data as ohms (e.g. DT9872).
		bool_ReturnsOhms,
       	
		// TRUE indicates that the subsystem supports multi-device synchronization
		bool_SupportsSynchronization,

		// TRUE indicates that the subsystem supports selectable thermocouple filtering
		bool_SupportsThermFilters,

		// TRUE indicates that the subsystem does not return raw counts but
		// only processed engineering units (e.g voltage, temperature).  True
		// for FlexarAD, TempPoint among others
		bool_SupportsNoRawData,

			// TRUE indicates that the subsystem supports selectable voltage ranges
		bool_SupportsVoltageRanges,

		// indicates that subsystem element belongs to an extended subsystem
		int_NumExtendedElements,
		
		// TRUE indicates that the subsystem supports Setting of the stale data flag
		bool_SupportsStaleDataFlag,

		// TRUE indicates that the hardware can run with external power or internal power
		// This is used to limit some options if the board is run using internal power
		bool_SupportsInternalAndExternalPower,
		
		bool_SupportsSoftwareReferenceTrigger,
		bool_SupportsPosExternalTTLReferenceTrigger,
		bool_SupportsNegExternalTTLReferenceTrigger,
		bool_SupportsPosThresholdReferenceTrigger,
		bool_SupportsNegThresholdReferenceTrigger,
		intArray_ThresholdReferenceTriggerSources,
		bool_SupportsPostReferenceTriggerScanCount,
		intArray_ThresholdSartTriggerSources,

		// Strain Gage support
		bool_SupportsStrainGage,
		bool_SupportsInternalExcitationVoltageSource,
		bool_SupportsExternalExcitationVoltageSource,
		double_MinExcitationVoltageValue,
		double_MaxExcitationVoltageValue,
		bool_SupportsShuntCalibration,
		bool_SupportsRemoteSense,

		bool_SupportsSyncBusReferenceTrigger,
		bool_SupportsMute,
		double_DefaultFrequency,
		bool_SupportsThermistor,
		bool_SupportsCurrent,
		bool_SupportsBridgeBasedSensors,
		bool_SupportsResistance,
		bool_SupportsMultiSensor,
		intArray_MultiSensorTypes,
		bool_SupportsIepe,
		bool_SupportsInputTermination,
		bool_SupportsMultiRecordAcquisition


// NOTE If you add any additional items here, you'll also need to update GetSubsystemCaps() 
// in oldaapi32.cpp
		
}CapCommand;

typedef enum
{
	NORMAL_HANDLE,
	QUERY_HANDLE
} HANDLE_TYPE;


#ifdef STRICT
 typedef BOOL (WINAPI* GETCHANNELMAPPING)(UINT uiType, CHAR *szBoardName, OLSS ss, UINT el, PCHANNELMAP_LIST pChannelMapList);
#else
 typedef FARPROC GETCHANNELMAPPING;
#endif

// name to use for GetProcAddress()
#ifdef _WIN64
#define GETCHANNELMAPPINGNAME  TEXT("GetChannelMapping")
#else
#define GETCHANNELMAPPINGNAME  TEXT("_GetChannelMapping@20")
#endif

#ifdef STRICT
 typedef bool (WINAPI* GETCAPVALUE_BOOLEAN)(UINT uiType, OLSS ss, UINT el, CapCommand Command, bool *value);
#else
 typedef FARPROC GETCAPVALUE_BOOLEAN;
#endif

#ifdef _WIN64
#define GETCAPVALUE_BOOLEANNAME  TEXT("GetCapValueBoolean")
#else
#define GETCAPVALUE_BOOLEANNAME  TEXT("_GetCapValueBoolean@20")
#endif

#ifdef STRICT
 typedef bool (WINAPI* GETCAPVALUE_INT)(UINT uiType, OLSS ss, UINT el, CapCommand Command, int *value);
#else
 typedef FARPROC GETCAPVALUE_INT;
#endif

#ifdef _WIN64
#define GETCAPVALUE_INTNAME  TEXT("GetCapValueInt")
#else
#define GETCAPVALUE_INTNAME  TEXT("_GetCapValueInt@20")
#endif

#ifdef STRICT
 typedef bool (WINAPI* GETCAPVALUE_UINT)(UINT uiType, OLSS ss, UINT el, CapCommand Command, UINT *value);
#else
 typedef FARPROC GETCAPVALUE_UINT;
#endif

#ifdef _WIN64
#define GETCAPVALUE_UINTNAME  TEXT("GetCapValueUint")
#else
#define GETCAPVALUE_UINTNAME  TEXT("_GetCapValueUint@20")
#endif

#ifdef STRICT
 typedef bool (WINAPI* GETCAPVALUE_FLOAT)(UINT uiType, OLSS ss, UINT el, CapCommand Command, FLOAT *value);
#else
 typedef FARPROC GETCAPVALUE_FLOAT;
#endif

#ifdef _WIN64
#define GETCAPVALUE_FLOATNAME  TEXT("GetCapValueFloat")
#else
#define GETCAPVALUE_FLOATNAME  TEXT("_GetCapValueFloat@20")
#endif

#ifdef STRICT
 typedef bool (WINAPI* GETCAPVALUE_DOUBLE)(UINT uiType, OLSS ss, UINT el, CapCommand Command, DBL *value);
#else
 typedef FARPROC GETCAPVALUE_DOUBLE;
#endif

#ifdef _WIN64
#define GETCAPVALUE_DOUBLENAME  TEXT("GetCapValueDouble")
#else
#define GETCAPVALUE_DOUBLENAME  TEXT("_GetCapValueDouble@20")
#endif


#ifdef STRICT
 typedef bool (WINAPI* GETCAPVALUES_BOOLEAN)(UINT uiType, OLSS ss, UINT el, CapCommand Command, PINT pNumItems, bool **ppValues);
#else
 typedef FARPROC GETCAPVALUES_BOOLEAN;
#endif

#ifdef _WIN64
#define GETCAPVALUES_BOOLEANNAME  TEXT("GetCapValuesBoolean")
#else
#define GETCAPVALUES_BOOLEANNAME  TEXT("_GetCapValuesBoolean@24")
#endif

#ifdef STRICT
 typedef bool (WINAPI* GETCAPVALUES_INT)(UINT uiType, OLSS ss, UINT el, CapCommand Command, PINT pNumItems, PINT *ppValues);
#else
 typedef FARPROC GETCAPVALUES_INT;
#endif

#ifdef _WIN64
#define GETCAPVALUES_INTNAME  TEXT("GetCapValuesInt")
#else
#define GETCAPVALUES_INTNAME  TEXT("_GetCapValuesInt@24")
#endif

 #ifdef STRICT
 typedef bool (WINAPI* GETCHANNELCAPVALUES_INT)(UINT uiType, OLSS ss, UINT el, UINT channel, CapCommand Command, PINT pNumItems, PINT *ppValues);
#else
 typedef FARPROC GETCHANNELCAPVALUES_INT;
#endif

#ifdef _WIN64
#define GETCHANNELCAPVALUES_INTNAME  TEXT("GetChannelCapValuesInt")
#else
#define GETCHANNELCAPVALUES_INTNAME  TEXT("_GetChannelCapValuesInt@28")
#endif

#ifdef STRICT
 typedef bool (WINAPI* GETCAPVALUES_UINT)(UINT uiType, OLSS ss, UINT el, CapCommand Command, PINT pNumItems, PUINT *ppValues);
#else
 typedef FARPROC GETCAPVALUES_UINT;
#endif

#ifdef _WIN64
#define GETCAPVALUES_UINTNAME  TEXT("GetCapValuesUint")
#else
#define GETCAPVALUES_UINTNAME  TEXT("_GetCapValuesUint@24")
#endif


#ifdef STRICT
 typedef bool (WINAPI* GETCAPVALUES_DOUBLE)(UINT uiType, OLSS ss, UINT el, CapCommand Command, PINT pNumItems, PDBL *ppValues);
#else
 typedef FARPROC GETCAPVALUES_DOUBLE;
#endif

// name to use for GetProcAddress()
#ifdef _WIN64
#define GETCAPVALUES_DOUBLENAME  TEXT("GetCapValuesDouble")
#else
#define GETCAPVALUES_DOUBLENAME  TEXT("_GetCapValuesDouble@24")
#endif

#ifdef STRICT
 typedef bool (WINAPI* GETCAPVALUE_INT)(UINT uiType, OLSS ss, UINT el, CapCommand Command, int *value);
#else
 typedef FARPROC GETCAPVALUE_INT;
#endif

#ifdef _WIN64
#define GETCAPVALUE_INTNAME  TEXT("GetCapValueInt")
#else
#define GETCAPVALUE_INTNAME  TEXT("_GetCapValueInt@20")
#endif

#ifdef STRICT
 typedef bool (WINAPI* GETCHANNELCAPVALUE_BOOLEAN)(UINT uiType, OLSS ss, UINT el, UINT channel, CapCommand Command, bool *value);
#else
 typedef FARPROC GETCHANNELCAPVALUE_BOOLEAN;
#endif

#ifdef _WIN64
#define GETCHANNELCAPVALUE_BOOLEANNAME  TEXT("GetChannelCapValueBoolean")
#else
#define GETCHANNELCAPVALUE_BOOLEANNAME  TEXT("_GetChannelCapValueBoolean@24")
#endif
 // An HDEV as returned from oldaInitialize actually points to one of these

typedef struct boarddata_tag 
{
   PVOID       pSelf;
   HINSTANCE   hPersonalityDll;             // from LoadLibrary call
   PERSONALITYPROCEX pfnPersonalityProcEx;
   UINT        uiUseCount;                  // cannot be freed unless this is zero
   UINT        uiBoardType;                 // from "Type" in registry
   PUINT       pDevCounts;                  // filled in by BoardInfoProc(), storage in Personality DLL
   TCHAR       szDriverName[64];			
   TCHAR       szUserName[64];              // Open Layers Board Name    
   TCHAR       szDeviceInterfacePath[128];  // Base Name of Symbolic Links to Driver 
   PTSTR       pszDeviceName;               // Device Name ( i.e. Model Name ), storage in personality DLL 
   HANDLE      hDrv;                        // returned by CreateFile() - for driver IOCTLs not subsystem-specific
   DWORD       StartSleepTimeMSecs;			// read from registry or 0
   DWORD       StopSleepTimeMSecs;			// read from registry or 0
   DWORD       NonBlockingStop;			    // Read from registry or 0
   DWORD       MessageOnAbort;			    // Read from registry or 0
   DWORD       AbortSleepTimeMSecs;		    // Read from registry or 0
   DWORD       CopyThreadPriority;		    // Read from registry or 0
   GETCAPVALUE_BOOLEAN pfnGetCapValue_boolean;
   GETCAPVALUE_DOUBLE pfnGetCapValue_double;
   GETCAPVALUES_DOUBLE pfnGetCapValues_double;
   GETCAPVALUE_INT pfnGetCapValue_int;
   GETCHANNELMAPPING pfnGetChannelMap;
   PEXTENDED_SS pExtendedSubsystems;
   DEVICE_CAPS   DeviceCaps;
	GETCAPVALUES_INT pfnGetCapValues_int;
	GETCHANNELCAPVALUES_INT pfnGetChanCapValues_int;
	GETCHANNELCAPVALUE_BOOLEAN pfnGetChanCapValue_boolean;

} 
BOARD_DATA, *PBOARD_DATA;


// A DASS as returned by oldaGetDASS actually points to one of these

typedef struct device_data_tag 
{
   PVOID        pSelf;                 // self reference for reality checks
   HANDLE       hDevice;               // cookie returned by CreateFile()
   PBOARD_DATA  pBoard;                // pointer to board information
   PERSONALITY  Personality;           // embedded structure containing device personality information
   TCHAR        szSubSystemName[64];   // subsystem name 
   OLSS         ss;                    // subsystem type
   UINT         el;                    // subsystem element
   PDEVICE_CFG  pCfgData;              // must be filled with default settings
   PDEVICE_CFG_EX pCfgDataEx;		   // Extended config info
   HLIST        hReady;                // Ready Queue, must be allocated
   HLIST        hDone;                 // Done Queue, must be allocated
   HANDLE       hThreadId;             // real time thread for copying data
   HANDLE       hThreadEvent;
   HANDLE       hThreadAckEvent;
   UINT         uiMsg;    
   CRITICAL_SECTION  csDevLock;

   CDtDataCopyThread*	pCopyThreadObject;			// copy thread
   HANDLE				hCopyThreadStartSyncEvent;	// to determine when copy thread is ready
   
   HWND         hWndNotify;
   WPARAM       wWndNotifyData;
   LPARAM       lWndNotifyData;
   OLNOTIFYPROC pfnNotify;
   WPARAM       wProcNotifyData;
   LPARAM       lProcNotifyData;
   HBUF         hFlushBuf;
   ULONG        ulFlushSamples;
   PIEPE_CONFIGLIST  pIepeConfigList;
   SUBSYSTEM_CAPS   SubsystemCaps;
   CHANNELMAP_LIST ChannelMap;
   HANDLE_TYPE	 HandleType;
   THERM_CONFIG_INFO ThermConfigInfo;
   PSTRAINCONFIG_LIST	pStrainConfig;
	SupportedChannels	SupportedChannels;
	
} DEVICE_DATA, *PDEVICE_DATA;  
 
#ifdef _DEBUG
#define Oops(string) OutputDebugString(TEXT(string))
#else
#define Oops(string)
#endif


#define AreLargeIntsEqual(x,y) (x.QuadPart == y.QuadPart)

#define LARGEST_32BIT_VALUE  4294967295.0

#define CONVERT_DBL_TO_LARGE_INT(dbl,large_int) { large_int.HighPart =((LONG)(int)dbl); \
                                                  large_int.LowPart = (LONG)((dbl - (int)dbl) * LARGEST_32BIT_VALUE); \
                                                }
#define CONVERT_LARGE_INT_TO_DBL(large_int,dbl) { dbl = (double)large_int.HighPart + \
                                                     ((ULONG)large_int.LowPart / LARGEST_32BIT_VALUE); \
                                                }
#define CONVERT_LARGE_INT_TO_DBL_RANGE(large_int,dbl) { dbl = (double)large_int.HighPart + \
                                                     ((LONG)large_int.LowPart / LARGEST_32BIT_VALUE); \
                                                }
        // JSJ Modified to Support NEG DECIMAL LARGE INTS

#define GetMemory(size) (PVOID)GlobalAlloc(GPTR,size)
#define ReleaseMemory(ptr) GlobalFree((HGLOBAL)ptr)

#define StaleFlagEnBit  (1 << 0)





                                                
#endif
