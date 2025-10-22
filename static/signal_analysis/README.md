# Compile instructions for shared library file (.so)
1) **Pre-req**: GCC compiler should be installed and the dt9837 C file should be present with the SDK files
2) Run the following command in the console from the signal_analysis folder
```
gcc .\dt9837.c -fPIC -shared -L./sdk_lib_files/Lib64 -lGraph64 -loldaapi64 -lOLMEM64 -I./sdk_lib_files/Include -o dt9837_lib.so
```

**Additionally, if there are issues running the DT9837 driver with relation to ctype CDLL issues, try installing the following. 

Install the DataAcqSDK from the following link/location:
C:\Automation_Framework\DataAcqOMNI_V7.8.9.zip

Install the following C++ distributable from Microsoft:
https://www.microsoft.com/en-us/download/details.aspx?id=53587