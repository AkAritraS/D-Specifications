

=====================================
DELTA SPECIFICATIONS 
Delta Industries (c) 2021
=====================================



D-S refers to Device Specification
Version - D-S 1.0
Code Name - FreddyWorm

Features available:
	- Device Stats
	- Date & Time
	- Pointer Controls
	- DOS Utility
	- CPS Test
	- FPS Test
	- .cur Support
	- System Summary
	- Temp-Terminator
	- Flush DNS


!!ONLY FOR DEVELOPER PURPOSES!!
import os
import platform
import psutil
import threading
import time
import subprocess
import sys
import ctypes
from datetime import datetime
from collections import deque

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog