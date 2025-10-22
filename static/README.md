# Description
This is the directory to keep all static that are required by certain scripts (eg: current consumption classification) that are used by the typical workflow of the framework.

Purpose of this area is to place any static files that need to remain in the framework. Typically these will be files that are used by modules of the framework, some examples include:
 - Reference graphs for classification during current consumption measurement. (TestSuite_CC)
 - Measurement file that is overwritten everytime a tool runs (PPKII)
 - Shared library file (.so, .dll) used by certain scripts (DT9837)

# Best practices:
  1. Create new directory for each type of file (under static) that contains relevant data / template / report
  2. Add a README.md file for each folder briefly explaining the purpose of the included files
  3. Use a proper naming convention and include explainations of abbreviations in the readme
  4. Have fun scripting!
