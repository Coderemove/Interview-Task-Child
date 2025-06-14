# Interview-Task-Child
Interview Task for My Thriving Task

# Dependencies:
 - Python 3.13.4+ - https://www.python.org/downloads/
 - Quarto -https://quarto.org/docs/get-started/
 - R 4.5.1 - https://cran.r-project.org/bin/windows/base/

# How to run:
Open up R if you never installed it before. (You can close it afterwards).
Install the dependencies and download the repository.
Add the data to the dataset folder.
Run the master.ipy
The report and dashboard should automatically open in your browser, both as HTML files.

# Common Errors
1. "'sh' is not recognized as an internal or external command,
    operable program or batch file."
This error occurs when you don't have a valid shell installed. Install RTools https://cran.r-project.org/bin/windows/Rtools/rtools45/rtools.html or another shell like Git Bash or Cygwin.

2. "FileNotFoundError: [WinError 2] The system cannot find the file specified"
This error occurs when Windows is being a bit...difficult with the system environment variables. You need to go to the System Environment Variables (Press Windows Key + S, and type "Environment Variables"). In it, remove from the User's PATH variable any mention of R. Remove RHome in the User's Enviroment Variables. Then, go to the System Path variable and add the R bin folder (e.g., C:\Program Files\R\R-4.5.1\bin\x64) to the PATH variable. Also, add RHome to the System Environment by adding your R install folder (e.g., C:\Program Files\R\R-4/5.1) **Restart your computer after making these changes.**

# Debugging:
 - If you encounter any issues, please check the Python version and ensure all dependencies are installed correctly.
 - If you have any questions, feel free to reach out to the repository owner.
 - Attach the latest log file if you encounter any issues when reporting issues.
