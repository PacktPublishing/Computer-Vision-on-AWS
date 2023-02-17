@ECHO OFF
@ECHO ==================================
@ECHO Deployment Tool
@ECHO Nate Bachmeier - Amazon Solutions
@ECHO ==================================

@SETLOCAL enableextensions enabledelayedexpansion
@SET base_path=%~dp0
@PUSHD %base_path%

@CALL docker build -t video-producer .
@CALL docker run -it --env-file debug.env -v %userprofile%\.aws:/root/.aws --entrypoint /var/task/app.py video-producer

@POPD