#if !defined(__TEDSAPI__)
#define __TEDSAPI__

/*-----------------------------------------------------------------------

FILE NAME: tedsapi.h

ABSTRACT:

	This unit contains declarations associated with TEDS.

---------------------------------------------------------------------------*/


// An identification number at the beginning of each template that identifies the template.
typedef enum 
{
	// No Template associated with the channel
	NotDefined = -1,
	
	// Bridfe Sensor
	BridgeSensors = 33,
	
	// Strain Gage
	StrainGage = 35
}TedsTemplateId;


// Physical Measurand (Units)
typedef enum 
{
	
	// Temperature (kelvin)
	Temperature_Kelvin,
	
	// Temperature (Celsius)
	Temperature_Celsius,
	
	// Strain
	Strain,
	
	// microstrain
	Microstrain,
	
	// Force/Weight (Newton)
	Newton,
	
	// Force/Weight (pounds)
	Pounds,
	
	// Force/Weight (kilogram-force/kilopond)
	kilogramForcePerKilopound,
	
	// Acceleration (m/s²)
	Acceleration_m_ss,
	
	// Acceleration (g)
	Acceleration_g,
	
	// Torque (Nm/radian)
	Torque_Nm_Radian,
	
	// Torque (Nm)
	Torque_Nm,
	
	// Torque (oz-in)
	Torque_oz_in,
	
	// Pressure (Pascal)
	Pressure_Pascal,
	
	// Pressure (PSI)
	Pressure_PSI,
	
	// Mass (kg)
	Mass_Kg,
	
	// Mass (g)
	Mass_g,
	
	// Distance (m)
	Distance_m,
	
	// Distance (mm)
	Distance_mm,
	
	// Distance (inches)
	Distance_inches,
	
	// Velocity (m/s)
	Velocity_m_s,
	
	// Velocity (mph)
	Velocity_mph,
	
	// Velocity (fps)
	Velocity_fps,
	
	// Angular Position (radian)
	AngularPosition_radian, 
	
	// Angular Position (degrees)
	AngularPosition_degrees,
	
	// Rotational Velocity (radian/s)
	RotationalVelocity_radian_s, 
	
	// Rotational Velocity (rpm)
	RotationalVelocity_rpm,
	
	// Frequency
	Frequency, 
	
	// Concentration (gram/liter)
	Concentration_gram_liter,
	
	// Concentration (kg/liter)
	Concentration_kg_liter, 
	
	// Molar Concentration (mole/m³)
	MolarConcentration_mole_m3,
	
	// Molar Concentration (mole/l)
	MolarConcentration_mole_l,
	
	// Volumetric Concentration (m³/m³)
	VolumetricConcentration_m3_m3, 
	
	// "Volumetric Concentration (l/l)
	VolumetricConcentration_l_l,
	
	// Mass Flow
	MassFlow,
	
	// Volumetric Flow (m³/s)
	VolumetricFlow_m3_s, 
	
	// Volumetric Flow (m³/hr)
	VolumetricFlow_m3_hr,
	
	// Volumetric Flow (gpm)
	VolumetricFlow_gpm, 
	
	// Volumetric Flow (cfm)
	VolumetricFlow_cfm,
	
	// Volumetric Flow (l/min)
	VolumetricFlow_l_min, 
	
	// Relative Humidity
	RelativeHumidity,
	
	// Ratio (percent)
	Ratio_percent, 
	
	// Voltage
	Voltage,
	
	// RMS Voltage
	RmsVoltage, 
	
	// Current
	Current,
	
	// RMS Current
	RmsCurrent, 
	
	// Power (Watts)
	Power_Watts
  
}PhysicalMeasurandUnits;

	
// Bridge types as defined by TEDS
typedef enum 
{
	// Quarter Bridge
	Quarter,
	
	// Half Bridge
	Half,
	
	// Full Bridge
	Full
}TedsBridgeType;


// Topology and rosette orientation of gage
typedef enum
{
	
	// Single element gage.
	SingleElement,
	
	// Two elements with a Poisson arrangement.
	TwoPoissonElements,
	
	// Two elements, opposite sign (adjacent arms).
	TwoOppositeSignedElements,
	
	// Two elements, same sign (opposite arms).
	TwoSameSignedElements,
	
	// Two elements, 45° Chevron (torque or shear) arrangement.
	TwoElementChevron,
	
	// Four elements, Poisson strains of same sign in opposite arms.
	FourSameSignElementsPoisson,
	
	// Four elements, Poisson strains of opposite sign in adjacent arms.
	FourOppositeSignedElements,
	
	// Four elements, equal strains of opposite sign in adjacent arms.
	FourUniaxialElements,
	
	// Four elements, 45° Chevron (torque or shear) arrangement.
	FourElementDualChevron,
	
	// Tee Rosette grid 1 or a (0°).
	TeeRosetteGrid1_0Degrees,
	
	// Tee Rosette grid 2 or b (90°).
	TeeRosetteGrid2_90Degrees,
	
	// Delta Rosette grid 1 or a (0°).
	DeltaRosetteGrid1_0Degrees,
	
	// Delta Rosette grid 2 or b (60°).
	DeltaRosetteGrid2_60Degrees,
	
	// Delta Rosette grid 3 or c (120°).
	DeltaRosetteGrid3_120Degrees,
	
	// Rectangular Rosette grid 1 or a (0°).
	RectangularRosetteGrid1_0Degrees,
	
	// Rectangular Rosette grid 2 or a (45°).
	RectangularRosetteGrid2_45Degrees,
	
	// Rectangular Rosette grid 3 or a (90°).
	RectangularRosetteGrid3_90Degrees
} GageType;

// Strain Gage TEDS properties
typedef struct STRAIN_GAGE_TEDS_tag 
{
	// Basic TEDS
	INT manufacturerId;
	INT modelNumber;
	CHAR versionLetter;
	INT  versionNumber;
	UINT serialNumber;

	// Strain Gage TEDS
	FLT minPhysicalValue;
	FLT maxPhysicalValue;
	FLT minElecVal;
	FLT maxElecVal;
	GageType gageType;
	FLT gageFactor;
	FLT gageTransSens;
	FLT gageOffset;
	FLT poissonCoef;
	FLT youngsMod;
	FLT gageArea;
	TedsBridgeType tedsBridgeType;
	FLT sensorImped;
	DBL respTime;
	FLT exciteAmplNom;
	FLT exciteAmplMax;
	UINT calDaysSince1_1_1998;
	CHAR calInitials[3];
	UINT calPeriod;
	UINT measID;
} STRAIN_GAGE_TEDS, *PSTRAIN_GAGE_TEDS; 

// Bridge Sensors TEDS properties
typedef struct  BRIDGE_SENSOR_TEDS_tag 
{
	// Basic TEDS
	INT manufacturerId;
	INT modelNumber;
	CHAR versionLetter;
	INT  versionNumber;
	UINT serialNumber;

	// Bridge Sensor TEDS
	UINT calDaysSince1_1_1998;
	CHAR calInitials[3];
	UINT calPeriod;
	FLT exciteAmplMax;
	FLT exciteAmplMin;
	FLT exciteAmplNom;
	FLT maxElecVal;
	FLT maxPhysicalValue;
	UINT measID;
	FLT minElecVal;
	FLT minPhysicalValue;
	PhysicalMeasurandUnits physicalMeasurand;
	DBL respTime;
	UINT selector;
	FLT sensorImped;
	TedsBridgeType tedsBridgeType;
} BRIDGE_SENSOR_TEDS, *PBRIDGE_SENSOR_TEDS; 

// Basic TEDS
typedef struct  BASIC_TEDS_tag 
{
	UINT manufacturerId;
	UINT modelNumber;
	CHAR versionLetter;
	UINT  versionNumber;
	UINT serialNumber;

} BASIC_TEDS, *PBASIC_TEDS;
 
#endif
