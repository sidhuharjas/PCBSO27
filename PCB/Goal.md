I want a pcb:
I will be running on 8 aa bateries

here are emotrs I will be using ecko Drive Motor Specs: https://justcuzrobotics.com/products/dartbox-gecko?variant=45733582274869
Dimensions (Drive): CAD Assembly Here
DartBox Diameter: 22mm
Gear Ratio: 22.5:1
Length: 46.5mm from the face. Gearbox 19.4mm + Motor 27.1mm
Shaft: 24mm long, steel D shaft
4X M2 Screw face mount, 18mm bolt circle
Weight:
53.7 grams (1.89 oz) with Gecko 4mm Shaft
56.0 grams (1.97 oz) with a 6mm Shaft
32 grams (1.41 oz) for bare DartBox Drive gearbox
Speed:
1100 +/- 55 RPM Max @ 12V / 3S
~1520 RPM Max @ 16V / 4S
~1900 RPM Max @ 20V / 5S
~2350 RPM Max @ 24V / 6S
Stall Torque: (Measured on one motor, results may vary)
11.1V / 3S: 58 ozf-in (4.2 kgf-cm)
14.6V / 4S: 63.2 ozf-in (4.6 kgf-cm)
24V / 6S: To Be Tested
Stall Current:
3.5A at 11.1V (3S nominal)
4.5A at 14.6V (4S nominal)
8A at 24V

ESC:
nput voltage: 7.5V - 30V (2S to 6S LiHV battery)
Weight: 3g with no wires, about 12g with included wires/connectors
Channels: 2
Motor type: brushed
Maximum continuous current per channel: 20 amps
First ESC with "Simon Says" calibration for motor direction, mixing and braking
Reversible: yes
Braking: yes (optional)
Mixing: yes (optional)
Current Limiting (will prevent damaging the ESC by limiting motor current, but will not protect motors from overheating)
Overtemp and Overcurrent protection
Low Voltage Cutoff
PCB size: 30 x 20 x 3.5mm [CAD file here]
BEC (Battery Eliminator Circuit/regulator): +5V 150mA regulator
Usage









Q&A






Customehttps://justcuzrobotics.com/products/weka-dual-20-esc-for-brushed-drive

rp235 microcontroler: [text](c:/Users/HARJAS/Downloads/RP-008373-DS-3-rp2350-datasheet.pdf) (can get the microcontroler assembled version if better)

AS5600 MAGnertic encoder
and witmotion901n encoder "C:\Users\HARJAS\Downloads\WT901-Datasheet.pdf"
switch to trige rmotion yk 2pcs 12mm Super Short Metal Momentary Push Button Switch Waterproof Anti-Vandal Flat Head Silver Shell 1/2" Mounting Hole with Pre-soldered Cable 12V 24V 110V (ON)-Off 2Pins 1NO

and display waveshare 1.69inch LCD Display Module 240×280 Resolution 262K Display Colors IPS Screen for Raspberry Pi, Arduino, STM32,Embedded ST7789V2 Driver Chip,SPI InterfaceNavigation menu
Waveshare Wiki
Raspberry Pi 
AI 
Displays 
IoT 
Robotics 
MCU/FPGA 
Support
Product name search
1.69inch LCD Module
1.69inch LCD Module
1.69inch LCD Module.jpg

1.69inch, 240 x 280, SPI
Overview
Specifications
Operating voltage: 3.3V/5V (Please ensure that the power supply voltage and logic voltage are the same, otherwise it will not work properly.)
Communication interface: SPI
Display Panel: IPS
Control chip: ST7789V2
Resolution: 240 (H)RGB × 280(V)
Display size: 27.972mm × 32.634mm
Display R angle: 4-R5 (mm)
Pixel pitch: 0.11655mm × 0.11655mm
Dimensions: 31.5mm × 39.0mm
Module & Control Chip
The embedded controller used in this module is ST7789V2, an LCD controller with 240 × RGB × 320 pixels, and the pixels of the LCD itself is 240(H) × RGB × 280(V), so the internal RAM of the LCD is not fully used.
This LCD supports input color formats of 12-bit, 16-bit, and 18-bit per pixel, which are RGB444, RGB565, and RGB666. This demo example uses the RGB565 color format, which is also a commonly used RGB format.
The LCD uses a four-wire SPI communication interface, which greatly saves GPIO ports with faster communication speeds.
TThe resolution of this module is 240 (H) x RGB x 280 (V), but due to the four round corners (see specifications for dimensions), some parts of the input images may not be displayed.
Communication Protocol
0.96inch lcd module spi.png
Note: The difference from the traditional SPI protocol is that the data line sent from the slave to the host is hidden because it only needs to be displayed. Please refer to Datasheet Page 66 for the table.
RESX is reset, it is pulled low when the module is powered on, usually set to 1;
CSX is the slave chip select, and the chip will be enabled only when CS is low.
D/CX is the data/command control pin of the chip, when DC = 0, write command, when DC = 1, write data.
SDA is the transmitted data, that is, RGB data;
SCL is the SPI communication clock.
For SPI communication, data is transmitted with timing, that is, the combination of clock phase (CPHA) and clock polarity (CPOL):
The level of CPHA determines whether the serial synchronization clock is collected on the first clock transition edge or the second clock transition edge. When CPHA = 0, data acquisition is performed on the first transition edge;
The level of CPOL determines the idle state level of the serial synchronous clock. CPOL = 0, which is a low level.
As can be seen from the figure, when the first falling edge of SCLK starts to transmit data, 8-bit data is transmitted in one clock cycle, using SPI0, bit-by-bit transmission, high-order first, and low-order last.

Raspberry Pi
Hardware Connection
When connecting to the Raspberry Pi, you can choose the 8PIN cable to connect according to the following table:

Raspberry Pi Connection Pin Correspondence
LCD	Raspberry Pi
BCM2835	Board
VCC	3.3V	3.3V
GND	GND	GND
DIN	MOSI	19
CLK	SCLK	23
CS	CE0	24
DC	25	22
RST	27	13
BL	18	12
The 1.69inch LCD uses the GH1.25 8PIN interface, which can be connected to the Raspberry Pi according to the above table: (Please connect according to the pin definition table. The color of the wiring in the picture is for reference only, and the actual color shall prevail.)
RPI for 1.69 lcd module01.jpg

Enable SPI Interface
Open the terminal, use the command to enter the configuration page:
sudo raspi-config
Choose Interfacing Options -> SPI -> Yes  to enable SPI interface
RPI open spi.png
Reboot Raspberry Pi：

sudo reboot
Check /boot/config.txt and you can see that 'dtparam=spi=on' has been written.
Raspberry Pi Guides for 4.37 e-Paper.jpg

To make sure that the SPI is not occupied, it is recommended that other driver overrides be turned off for now. You can use ls /dev/spi* to check the SPI occupancy. The terminal output /dev/spidev0.0 and /dev/spidev0.1 indicates that the SPI status is normal.
Raspberry Pi Guides for 4.37 e-Paper02.jpg

Running C Demo
Install BCM2835
# Open the Raspberry Pi terminal and run the following command:
wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.71.tar.gz
tar zxvf bcm2835-1.71.tar.gz 
cd bcm2835-1.71/
sudo ./configure && sudo make && sudo make check && sudo make install
# For more information, please refer to the official website: http://www.airspayce.com/mikem/bcm2835/
Indtall wiringPi
# Open the Raspberry Pi terminal and run the following command:
sudo apt-get install wiringpi
#For Raspberry Pi systems after May 2019 (earlier than that can be executed without), an upgrade may be required:
wget https://project-downloads.drogon.net/wiringpi-latest.deb
sudo dpkg -i wiringpi-latest.deb
gpio -v
# Run gpio -v and version 2.52 will appear, if it does not, there was an installation error.

# Bullseye branch system using the following command:
git clone https://github.com/WiringPi/WiringPi
cd WiringPi
. /build
gpio -v
# Run gpio -v and version 2.60 will appear, if it doesn't, there is an installation error.
Install lgpio:
#Open the Raspberry Pi terminal and run the following commands:
wget https://github.com/joan2937/lg/archive/master.zip
unzip master.zip
cd lg-master
sudo make install

#For more details, you can refer to the official website: https://github.com/gpiozero/lg
Download the Demo
sudo apt-get install unzip -y
sudo wget https://files.waveshare.com/upload/8/8d/LCD_Module_RPI_code.zip
sudo unzip LCD_Module_RPI_code.zip 
cd LCD_Module_RPI_code/RaspberryPi/
Recompile, the compilation process may take a few seconds:
cd c
sudo make clean
sudo make -j 8
Test procedures for all screens can be called directly by entering the corresponding size:

sudo ./main 1.69
Run Python Demo
Install library:
sudo apt-get update
sudo apt-get install python3-pip
sudo apt-get install python3-pil
sudo apt-get install python3-numpy
sudo pip3 install spidev
Download the demo:
sudo apt-get install unzip -y
sudo wget https://files.waveshare.com/upload/8/8d/LCD_Module_RPI_code.zip
sudo unzip LCD_Module_RPI_code.zip 
cd LCD_Module_RPI_code/RaspberryPi/
Enter the python demo directory and run the "ls -l" commands:
cd python/example
ls -l
RPI for 1.69 lcd module03.jpg
All test demos for screens can be viewed, sorted by size:

0inch96_LCD_test.py 0.96inch LCD test demo
1inch14_LCD_test.py 1.14inch LCD test demo
1inch28_LCD_test.py 1.28inch LCD test demo
1inch3_LCD_test.py 1.3inch LCD test demo
1inch47_LCD_test.py 1.47inch LCD test demo
1inch54_LCD_test.py 1.54inch LCD test demo
1inch69_LCD_test.py 1.69inch LCD test demo
1inch8_LCD_test.py 1.8inch LCD test demo
1inch9_LCD_test.py 1.9inch LCD test demo
2inch_LCD_test.py 2inch LCD test demo
2inch4_LCD_test.py 2.4inch LCD test demo
Just run the demo corresponding to the screen, the demo supports python2/3.

# python2
sudo python 1inch69_LCD_test.py
# python3
sudo python3 1inch69_LCD_test.py
FBCP Porting
Framebuffer uses a video output device to drive a video display device from a memory buffer containing complete frame data. Simply put, a memory area is used to store the display content, and the display content can be changed by changing the data in the memory.
There is an open source project on github: fbcp-ili9341. Compared with other fbcp projects, this project uses partial refresh and DMA to achieve a speed of up to 60fps.

Download Drivers
sudo apt-get install cmake -y
cd ~
wget https://files.waveshare.com/upload/1/18/Waveshare_fbcp.zip
unzip Waveshare_fbcp.zip
cd Waveshare_fbcp/
sudo chmod +x ./shell/*
Method 1: Use a script (recommended)
Here we have written several scripts that allow users to quickly use fbcp and run corresponding commands according to their own screen
If you use a script and do not need to modify it, you can ignore the second method below.
Note: The script will replace the corresponding /boot/config.txt and /etc/rc.local and restart, if the user needs, please back up the relevant files in advance.

#0.96inch LCD Module
sudo ./shell/waveshare-0inch96
#1.14inch LCD Module
sudo ./shell/waveshare-1inch14
#1.3inch LCD Module
sudo ./shell/waveshare-1inch3
#1.47inch LCD Module
sudo ./shell/waveshare-1inch47
#1.54inch LCD Module
sudo ./shell/waveshare-1inch54
#1.69inch LCD Module
sudo ./shell/waveshare-1inch69
#1.8inch LCD Module
sudo ./shell/waveshare-1inch8
#1.9inch LCD Module
sudo ./shell/waveshare-1inch9
#2inch LCD Module
sudo ./shell/waveshare-2inch
#2.4inch LCD Module
sudo ./shell/waveshare-2inch4
Method 2: Manual Configuration
Environment Configuration
Raspberry Pi's vc4-kms-v3d will cause fbcp to fail, so we need to close vc4-kms-v3d before installing it in fbcp.

sudo nano /boot/config.txt
Just block the statement corresponding to the picture below.
FBCP CLOSE.jpg
A reboot is then required.

sudo reboot
Compile and Run
mkdir build
cd build
cmake [options] ..
sudo make -j
sudo ./fbcp
Replace it by yourself according to the LCD Module you use, above cmake [options] ..

#0.96inch LCD Module
sudo cmake -DSPI_BUS_CLOCK_DIVISOR=20 -DWAVESHARE_0INCH96_LCD=ON -DBACKLIGHT_CONTROL=ON -DSTATISTICS=0 ..
#1.14inch LCD Module
sudo cmake -DSPI_BUS_CLOCK_DIVISOR=20 -DWAVESHARE_1INCH14_LCD=ON -DBACKLIGHT_CONTROL=ON -DSTATISTICS=0 ..
#1.3inch LCD Module
sudo cmake -DSPI_BUS_CLOCK_DIVISOR=20 -DWAVESHARE_1INCH3_LCD=ON -DBACKLIGHT_CONTROL=ON -DSTATISTICS=0 ..
#1.47inch LCD Module
sudo cmake -DSPI_BUS_CLOCK_DIVISOR=20 -DWAVESHARE_1INCH47_LCD=ON -DBACKLIGHT_CONTROL=ON -DSTATISTICS=0 ..
#1.54inch LCD Module
sudo cmake -DSPI_BUS_CLOCK_DIVISOR=20 -DWAVESHARE_1INCH54_LCD=ON -DBACKLIGHT_CONTROL=ON -DSTATISTICS=0 ..
#1.69inch LCD Module
sudo cmake -DSPI_BUS_CLOCK_DIVISOR=20 -DWAVESHARE_1INCH69_LCD=ON -DBACKLIGHT_CONTROL=ON -DSTATISTICS=0 ..
#1.8inch LCD Module
sudo cmake -DSPI_BUS_CLOCK_DIVISOR=20 -DWAVESHARE_1INCH8_LCD=ON -DBACKLIGHT_CONTROL=ON -DSTATISTICS=0 ..
#1.9inch LCD Module
sudo cmake -DSPI_BUS_CLOCK_DIVISOR=20 -DWAVESHARE_1INCH9_LCD=ON -DBACKLIGHT_CONTROL=ON -DSTATISTICS=0 ..
#2inch LCD Module
sudo cmake -DSPI_BUS_CLOCK_DIVISOR=20 -DWAVESHARE_2INCH_LCD=ON -DBACKLIGHT_CONTROL=ON -DSTATISTICS=0 ..
#2.4inch LCD Module
sudo cmake -DSPI_BUS_CLOCK_DIVISOR=20 -DWAVESHARE_2INCH4_LCD=ON -DBACKLIGHT_CONTROL=ON -DSTATISTICS=0 ..
Set up to Start Automatically
1in3 lcd fb5.png
sudo cp ~/Waveshare_fbcp/build/fbcp /usr/local/bin/fbcp
sudo nano /etc/rc.local
Add fbcp& before exit 0. Note that you must add "&" to run in the background, otherwise the system may not be able to start.

Set the Display Resolution
Set the user interface display size in the "/boot/config.txt" file.

sudo nano /boot/config.txt
Add the configuration statement for the resolution to the "config.txt" file.

hdmi_force_hotplug=1
hdmi_cvt=[options]
hdmi_group=2
hdmi_mode=1
hdmi_mode=87
display_rotate=0
Replace the above "hdmi_cvt=[options]" according to the LCD Module that you are using.

#2.4inchinch LCD Module & 2inchinch LCD Module
hdmi_cvt=640 480 60 1 0 0 0
#1.9inch LCD Module
hdmi_cvt 640 340 60 6 0 0 0
#1.8inch LCD Module
hdmi_cvt=400 300 60 1 0 0 0
#1.69inch LCD Module
hdmi_cvt 560 480 60 6 0 0 0
#1.47inch LCD Module
hdmi_cvt 640 344 60 6 0 0 0
#1.3inch LCD Module & 1.54inch LCD Module
hdmi_cvt 480 480 60 6 0 0 0
#1.14inch LCD Module
hdmi_cvt 480 270 60 6 0 0 0
#0.96inch LCD Module
hdmi_cvt 320 160 60 6 0 0 0
And then reboot the system:

sudo reboot
After rebooting the system, the Raspberry Pi OS user interface will be displayed.

800px-2inch OLED01 fbcp.png

STM32
Hardware Connection
The demo we provided is based on STM32F103RBT6 and the connections provided correspond to the pins of the STM32F103RBT6, so if you need to port the demo, please connect the pins according to the actual pins:

STM32F103ZET Pin
LCD	STM32
VCC	3.3V
GND	GND
DIN	PA7
CLK	PA5
CS	PB6
DC	PA8
RST	PA9
BL	PC7
Taking the XNUCLEO-F103RB development board developed by our company as an example, the connection is as follows:
Arduino for 1.69 lcd module02.jpg

Run the Demo
Download the demo and find the STM32 demo file directory, open "LCD_demo.uvprojx" in the directory of "STM32\STM32F103RBT6\MDK-ARM", and then you can see the project.
LCD STM32 CODE1.png

Open "main.c" and you can see all the test demos.
As the demo we used is the 1.69-inch LCD module, you need to remove the comment in front of "LCD_1in69_test()"; and recompile and download it.
Stm32 for 1.69 lcd module 04.jpg

Demo Description
Underlying Hardware Interface
Data type:
#define UBYTE      uint8_t
#define UWORD      uint16_t
#define UDOUBLE    uint32_t
How to initialize and exit the module:
void DEV_Module_Init(void);
void DEV_Module_Exit(void);
Note: 
1. Here is some GPIO processing before and after using the LCD screen.
2. After the System_Exit(void) function is used, the OLED display will be turned off;
Write and read GPIO:
void 	DEV_Digital_Write(UWORD Pin, UBYTE Value);
UBYTE 	DEV_Digital_Read(UWORD Pin);
SPI writes data:
void    DEV_SPI_WRITE(UBYTE _dat);
Upper Application
For the screen, if you need to draw pictures, display Chinese and English characters, display pictures, etc., you can use the upper application to do, and we provide some basic functions here about some graphics processing in the directory STM32\STM32F103RB\User\GUI_DEV\GUI_Paint.c(.h).
Note: Because of the size of the internal RAM of STM32 and Arduino, the GUI is directly written to the RAM of the LCD.
LCD rpi GUI.png
The character font on which GUI dependent is in the directory STM32\STM32F103RB\User\Fonts
LCD rpi Font.png

New Image Properties: Create a new image property, this property includes the image buffer name, width, height, flip Angle, and color.
void Paint_NewImage(UWORD Width, UWORD Height, UWORD Rotate, UWORD Color)
Parameters:
    Width: image buffer Width;
    Height: the Height of the image buffer;
    Rotate: Indicates the rotation Angle of an image
    Color: the initial Color of the image;
Set the clear screen function, usually call the clear function of LCD directly.
void Paint_SetClearFuntion(void (*Clear)(UWORD));
parameter:
    Clear: Pointer to the clear screen function, used to quickly clear the screen to a certain color;
Set the drawing pixel function
void Paint_SetDisplayFuntion(void (*Display)(UWORD,UWORD,UWORD));
parameter:
    Display: Pointer to the pixel drawing function, which is used to write data to the specified location in the internal RAM of the LCD;
Select image buffer: the purpose of the selection is that you can create multiple image attributes, an image buffer can exist multiple, and you can select each image you create.
void Paint_SelectImage(UBYTE *image)
Parameters:
    Image: the name of the image cache, which is actually a pointer to the first address of the image buffer
Image Rotation: Set the selected image rotation Angle, preferably after Paint_SelectImage(), you can choose to rotate 0, 90, 180, 270.
Rotation-lcd.png

void Paint_SetRotate(UWORD Rotate)
Parameters:
    Rotate: ROTATE_0, ROTATE_90, ROTATE_180, and ROTATE_270 correspond to 0, 90, 180, and 270 degrees respectively;
Image mirror flip: Set the mirror flip of the selected image. You can choose no mirror, horizontal mirror, vertical mirror, or image center mirror.
void Paint_SetMirroring(UBYTE mirror)
Parameters:
    Mirror: indicates the image mirroring mode. MIRROR_NONE, MIRROR_HORIZONTAL, MIRROR_VERTICAL, MIRROR_ORIGIN correspond to no mirror, horizontal mirror, vertical mirror, and about image center mirror respectively.
Set points of display position and color in the buffer: here is the core GUI function, processing points display position and color in the buffer.
void Paint_SetPixel(UWORD Xpoint, UWORD Ypoint, UWORD Color)
Parameters:
    Xpoint: the X position of a point in the image buffer
    Ypoint: Y position of a point in the image buffer
    Color: indicates the Color of the dot
Image buffer fill color: Fills the image buffer with a color, usually used to flash the screen into blank.
void Paint_Clear(UWORD Color)
Parameters:
    Color: fill Color
Image buffer part of the window filling color: the image buffer part of the window filled with a certain color, generally as a window whitewashing function, often used for time display, whitewashing on a second
void Paint_ClearWindows(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD Color)
Parameters:
    Xstart: the x-starting coordinate of the window
    Ystart: indicates the Y starting point of the window
    Xend: the x-end coordinate of the window
    Yend: indicates the y-end coordinate of the window
    Color: fill Color
Draw points: In the image buffer, draw points on (Xpoint, Ypoint), you can choose the color, the size of the point, the style of the point.
void Paint_DrawPoint(UWORD Xpoint, UWORD Ypoint, UWORD Color, DOT_PIXEL Dot_Pixel, DOT_STYLE Dot_Style)
Parameters:
    Xpoint: indicates the X coordinate of a point
    Ypoint: indicates the Y coordinate of a point
    Color: fill Color
    Dot_Pixel: The size of the dot, providing a default of eight size points
        typedef enum {
            DOT_PIXEL_1X1   = 1,	// 1 x 1
            DOT_PIXEL_2X2  , 		// 2 X 2
            DOT_PIXEL_3X3  , 	 	// 3 X 3
            DOT_PIXEL_4X4  , 	 	// 4 X 4
            DOT_PIXEL_5X5  , 		// 5 X 5
            DOT_PIXEL_6X6  , 		// 6 X 6
            DOT_PIXEL_7X7  , 		// 7 X 7
            DOT_PIXEL_8X8  , 		// 8 X 8
        } DOT_PIXEL;
    Dot_Style: the size of a point that expands from the center of the point or from the bottom left corner of the point to the right and up
        typedef enum {
            DOT_FILL_AROUND  = 1,
            DOT_FILL_RIGHTUP,
        } DOT_STYLE;
Line drawing: In the image buffer, line from (Xstart, Ystart) to (Xend, Yend), you can choose the color, line width, line style.
void Paint_DrawLine(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD Color, LINE_STYLE Line_Style ,  LINE_STYLE Line_Style)
Parameters:
    Xstart: the x-starting coordinate of a line
    Ystart: indicates the Y starting point of a line
    Xend: x-terminus of a line
    Yend: the y-end coordinate of a line
    Color: fill Color
    Line_width: The width of the line, which provides a default of eight widths
        typedef enum {
            DOT_PIXEL_1X1   = 1,	// 1 x 1
            DOT_PIXEL_2X2  , 		// 2 X 2
            DOT_PIXEL_3X3  ,		// 3 X 3
            DOT_PIXEL_4X4  ,		// 4 X 4
            DOT_PIXEL_5X5  , 		// 5 X 5
            DOT_PIXEL_6X6  , 		// 6 X 6
            DOT_PIXEL_7X7  , 		// 7 X 7
            DOT_PIXEL_8X8  , 		// 8 X 8
        } DOT_PIXEL;
    Line_Style: line style. Select whether the lines are joined in a straight or dashed way
        typedef enum {
            LINE_STYLE_SOLID = 0,
            LINE_STYLE_DOTTED,
        } LINE_STYLE;
Draw a rectangle: In the image buffer, draw a rectangle from (Xstart, Ystart) to (Xend, Yend), you can choose the color, the width of the line, and whether to fill the inside of the rectangle.
void Paint_DrawRectangle(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD Color, DOT_PIXEL Line_width,  DRAW_FILL Draw_Fill)
Parameters:
        Xstart: the starting X coordinate of the rectangle
        Ystart: indicates the Y starting point of the rectangle
        Xend: X terminus of the rectangle
        Yend: specifies the y-end coordinate of the rectangle
        Color: fill Color
        Line_width: The width of the four sides of a rectangle. Default eight widths are provided
            typedef enum {
                DOT_PIXEL_1X1   = 1,	// 1 x 1
                DOT_PIXEL_2X2  , 		// 2 X 2
                DOT_PIXEL_3X3  ,		// 3 X 3
                DOT_PIXEL_4X4  ,		// 4 X 4
                DOT_PIXEL_5X5  , 		// 5 X 5
                DOT_PIXEL_6X6  , 		// 6 X 6
                DOT_PIXEL_7X7  , 		// 7 X 7
                DOT_PIXEL_8X8  , 		// 8 X 8
            } DOT_PIXEL;
        Draw_Fill: Fill, whether to fill the inside of the rectangle
            typedef enum {
                DRAW_FILL_EMPTY = 0,
                DRAW_FILL_FULL,
            } DRAW_FILL;
Draw circle: In the image buffer, draw a circle of Radius with (X_Center Y_Center) as the center. You can choose the color, the width of the line, and whether to fill the inside of the circle.
void Paint_DrawCircle(UWORD X_Center, UWORD Y_Center, UWORD Radius, UWORD Color, DOT_PIXEL Line_width,  DRAW_FILL Draw_Fill)
Parameters:
    X_Center: the x-coordinate of the center of a circle
    Y_Center: Y coordinate of the center of a circle
    Radius: indicates the Radius of a circle
    Color: fill Color
    Line_width: The width of the arc, with a default of 8 widths
        typedef enum {
            DOT_PIXEL_1X1  = 1,	        // 1 x 1
            DOT_PIXEL_2X2  , 		// 2 X 2
            DOT_PIXEL_3X3  ,		// 3 X 3
            DOT_PIXEL_4X4  ,		// 4 X 4
            DOT_PIXEL_5X5  , 		// 5 X 5
            DOT_PIXEL_6X6  , 		// 6 X 6
            DOT_PIXEL_7X7  , 		// 7 X 7
            DOT_PIXEL_8X8  , 		// 8 X 8
        } DOT_PIXEL;
    Draw_Fill: fill, whether to fill the inside of the circle
        typedef enum {
            DRAW_FILL_EMPTY = 0,
            DRAW_FILL_FULL,
        } DRAW_FILL;
Write Ascii character: In the image buffer, at (Xstart Ystart) as the left vertex, write an Ascii character, you can select Ascii visual character library, font foreground color, font background color.
void Paint_DrawChar(UWORD Xstart, UWORD Ystart, const char Ascii_Char, sFONT* Font, UWORD Color_Foreground,  UWORD Color_Background)
Parameters:
    Xstart: the x-coordinate of the left vertex of a character
    Ystart: the Y coordinate of the font's left vertex
    Ascii_Char: indicates the Ascii character
    Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
        Font8: 5*8 font
        Font12: 7*12 font
        Font16: 11*16 font
        Font20: 14*20 font
        Font24: 17*24 font
    Color_Foreground: Font color
    Color_Background: indicates the background color
Write English string: In the image buffer, use (Xstart Ystart) as the left vertex, write a string of English characters, can choose Ascii visual character library, font foreground color, font background color.
void Paint_DrawString_EN(UWORD Xstart, UWORD Ystart, const char * pString, sFONT* Font, UWORD Color_Foreground,  UWORD Color_Background)
Parameters:
    Xstart: the x-coordinate of the left vertex of a character
    Ystart: the Y coordinate of the font's left vertex
    PString: string, string is a pointer
    Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
        Font8: 5*8 font
        Font12: 7*12 font
        Font16: 11*16 font
        Font20: 14*20 font
        Font24: 17*24 font
     Color_Foreground: Font color
     Color_Background: indicates the background color
Write Chinese string: in the image buffer, use (Xstart Ystart) as the left vertex, and write a string of Chinese characters, you can choose GB2312 encoding character font, font foreground color, and font background color.
void Paint_DrawString_CN(UWORD Xstart, UWORD Ystart, const char * pString, cFONT* font, UWORD Color_Foreground,  UWORD Color_Background)
Parameters:
    Xstart: the x-coordinate of the left vertex of a character
    Ystart: the Y coordinate of the font's left vertex
    PString: string, string is a pointer
    Font: GB2312 encoding character Font library, in the Fonts folder provides the following Fonts:
        Font12CN: ASCII font 11*21, Chinese font 16*21
        Font24CN: ASCII font24 *41, Chinese font 32*41
    Color_Foreground: Font color
    Color_Background: indicates the background color
Write numbers: In the image buffer, use (Xstart Ystart) as the left vertex, and write a string of numbers, you can choose Ascii visual character library, font foreground color, or font background color.
void Paint_DrawNum(UWORD Xpoint, UWORD Ypoint, double Nummber, sFONT* Font, UWORD Digit, UWORD Color_Foreground,   UWORD Color_Background)
Parameters:
    Xpoint: the x-coordinate of the left vertex of a character
    Ypoint: the Y coordinate of the left vertex of the font
    Nummber: indicates the number displayed, which can be a decimal
    Digit: It's a decimal number
    Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
        Font8: 5*8 font
        Font12: 7*12 font
        Font16: 11*16 font
        Font20: 14*20 font
        Font24: 17*24 font
    Color_Foreground: Font color
    Color_Background: indicates the background color
Display time: in the image buffer, use (Xstart Ystart) as the left vertex, display time,you can choose Ascii visual character font, font foreground color, or font background color.
void Paint_DrawTime(UWORD Xstart, UWORD Ystart, PAINT_TIME *pTime, sFONT* Font, UWORD Color_Background,  UWORD Color_Foreground)
Parameters:
    Xstart: the x-coordinate of the left vertex of a character
    Ystart: the Y coordinate of the font's left vertex
    PTime: display time, here defined a good time structure, as long as the hour, minute and second bits of data to the parameter;
    Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
        Font8: 5*8 font
        Font12: 7*12 font
        Font16: 11*16 font
        Font20: 14*20 font
        Font24: 17*24 font
    Color_Foreground: Font color
    Color_Background: indicates the background color
Arduino
Note: all the demos have been tested on the Arduino uno, you need to make sure the connection is correct if you want to use other Arduino.

IDE Installation
How to install Arduino IDE

Hardware Connection
Arduino UNO Pins
LCD	UNO
VCC	5V
GND	GND
DIN	D11
CLK	D13
CS	D10
DC	D7
RST	D8
BL	D9
The connection diagram is as follows (click to enlarge):
Stm32 for 1.69 lcd module 02.jpg

Run the Demo
In the #Resource download the demo, and then unzip it. The Arduino demo is at ~/Arduino/…
LCD arduino cede1.png

The demo we used is 1.69inch LCD Module, so we need to open the LCD_1inch69 file folder and run the LCD_1inch69.ino file.
Arduino for 1.69inch lcd module06.jpg

Open the demo and chose the Dev board model as Arduino UNO.
Arduino for 1.69inch lcd module03.jpg

Choose the corresponding COM port.
Arduino for 1.69inch lcd module04.jpg

Then click to compile and download.
Arduino for 1.69inch lcd module05.jpg

Demo Description
Document Introduction
Take Arduino UNO controlling a 1.54-inch LCD as an example, open the Arduino\LCD_1inch54 directory:
LCD arduino ide codeDescription1.png
Of which:
LCD_1inch54.ino: open with Arduino IDE;
LCD_Driver.cpp(.h): is the driver of the LCD screen;
DEV_Config.cpp(.h): It is the hardware interface definition, which encapsulates the read and write pin levels, SPI transmission data, and pin initialization;
font8.cpp, font12.cpp, font16.cpp, font20.cpp, font24.cpp, font24CN.cpp, fonts.h: fonts for characters of different sizes;
image.cpp(.h): is the image data, which can convert any BMP image into a 16-bit true color image array through Img2Lcd (downloadable in the development data).
The demo is divided into bottom-layer hardware interface, middle-layer LCD screen driver, and upper-layer application.

Underlying Hardware Interface
The hardware interface is defined in the two files DEV_Config.cpp(.h), and functions such as read and write pin level, delay, and SPI transmission are encapsulated.

Write pin level:
void DEV_Digital_Write(int pin, int value)
The first parameter is the pin, and the second is the high and low levels.

Read pin level:
int DEV_Digital_Read(int pin)
The parameter is the pin, and the return value is the level of the read pin.

Delay:
DEV_Delay_ms(unsigned int delaytime)
millisecond level delay.

SPI output data:
DEV_SPI_WRITE(unsigned char data)
The parameter is char type, occupying 8 bits.

Upper Application
For the screen, if you need to draw pictures, display Chinese and English characters, display pictures, etc., you can use the upper application to do, and we provide some basic functions here about some graphics processing in the directory GUI_Paint.c(.h)
Note: Because of the size of the internal RAM of STM32 and Arduino, the GUI is directly written to the RAM of the LCD.
LCD arduino ide codeDescription GUI.png
The fonts used by the GUI all depend on the font*.cpp(h) files under the same file.
LCD arduino ide codeDescription font.png

New Image Properties: Create a new image property, this property includes the image buffer name, width, height, flip Angle, color.
void Paint_NewImage(UWORD Width, UWORD Height, UWORD Rotate, UWORD Color)
Parameters:
    Width: image buffer Width;
    Height: the Height of the image buffer;
    Rotate: Indicates the rotation Angle of an image
    Color: the initial Color of the image;
Set the clear screen function, usually call the clear function of LCD directly.
void Paint_SetClearFuntion(void (*Clear)(UWORD));
parameter:
    Clear: Pointer to the clear screen function, used to quickly clear the screen to a certain color;
Set the drawing pixel function.
void Paint_SetDisplayFuntion(void (*Display)(UWORD,UWORD,UWORD));
parameter:
    Display: Pointer to the pixel drawing function, which is used to write data to the specified location in the internal RAM of the LCD;
Select image buffer: the purpose of the selection is that you can create multiple image attributes, image buffer can exist multiple, and you can select each image you create.
void Paint_SelectImage(UBYTE *image)
Parameters:
    Image: the name of the image cache, which is actually a pointer to the first address of the image buffer
Image Rotation: Set the selected image rotation Angle, preferably after Paint_SelectImage(), you can choose to rotate 0, 90, 180, 270.
Rotation-lcd.png

void Paint_SetRotate(UWORD Rotate)
Parameters:
    Rotate: ROTATE_0, ROTATE_90, ROTATE_180, and ROTATE_270 correspond to 0, 90, 180, and 270 degrees respectively;
Image mirror flip: Set the mirror flip of the selected image. You can choose no mirror, horizontal mirror, vertical mirror,or image center mirror.
void Paint_SetMirroring(UBYTE mirror)
Parameters:
    Mirror: indicates the image mirroring mode. MIRROR_NONE, MIRROR_HORIZONTAL, MIRROR_VERTICAL, MIRROR_ORIGIN correspond to no mirror, horizontal mirror, vertical mirror, and about image center mirror respectively.
Set points of display position and color in the buffer: here is the core GUI function, processing points display position and color in the buffer.
void Paint_SetPixel(UWORD Xpoint, UWORD Ypoint, UWORD Color)
Parameters:
    Xpoint: the X position of a point in the image buffer
    Ypoint: Y position of a point in the image buffer
    Color: indicates the Color of the dot
Image buffer fill color: Fills the image buffer with a color, usually used to flash the screen into blank.
void Paint_ClearWindows(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD Color)
Parameters:
    Xstart: the x-starting coordinate of the window
    Ystart: indicates the Y starting point of the window
    Xend: the x-end coordinate of the window
    Yend: indicates the y-end coordinate of the window
    Color: fill Color
Draw points: In the image buffer, draw points on (Xpoint, Ypoint), you can choose the color, the size of the point, and the style of the point.
void Paint_DrawPoint(UWORD Xpoint, UWORD Ypoint, UWORD Color, DOT_PIXEL Dot_Pixel, DOT_STYLE Dot_Style)
Parameters:
    Xpoint: indicates the X coordinate of a point
    Ypoint: indicates the Y coordinate of a point
    Color: fill Color
    Dot_Pixel: The size of the dot, providing a default of eight size points
        typedef enum {
                DOT_PIXEL_1X1  = 1,	        // 1 x 1
                DOT_PIXEL_2X2  , 		// 2 X 2
                DOT_PIXEL_3X3  , 	 	// 3 X 3
                DOT_PIXEL_4X4  , 	 	// 4 X 4
                DOT_PIXEL_5X5  , 		// 5 X 5
                DOT_PIXEL_6X6  , 		// 6 X 6
                DOT_PIXEL_7X7  , 		// 7 X 7
                DOT_PIXEL_8X8  , 		// 8 X 8
        } DOT_PIXEL;
    Dot_Style: the size of a point that expands from the center of the point or from the bottom left corner of the point to the right and up
        typedef enum {
                DOT_FILL_AROUND  = 1,
                DOT_FILL_RIGHTUP,
        } DOT_STYLE;
Line drawing: In the image buffer, line from (Xstart, Ystart) to (Xend, Yend), you can choose the color, line width, and line style.
void Paint_DrawLine(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD Color, LINE_STYLE Line_Style ,  LINE_STYLE Line_Style)
Parameters:
        Xstart: the x-starting coordinate of a line
        Ystart: indicates the Y starting point of a line
        Xend: x-terminus of a line
        Yend: the y-end coordinate of a line
        Color: fill Color
        Line_width: The width of the line, which provides a default of eight widths
                typedef enum {
                        DOT_PIXEL_1X1  = 1,	        // 1 x 1
                        DOT_PIXEL_2X2  , 		// 2 X 2
                        DOT_PIXEL_3X3  ,		// 3 X 3
                        DOT_PIXEL_4X4  ,		// 4 X 4
                        DOT_PIXEL_5X5  , 		// 5 X 5
                        DOT_PIXEL_6X6  , 		// 6 X 6
                        DOT_PIXEL_7X7  , 		// 7 X 7
                        DOT_PIXEL_8X8  , 		// 8 X 8
                    } DOT_PIXEL;
        Line_Style: line style. Select whether the lines are joined in a straight or dashed way
                typedef enum {
                        LINE_STYLE_SOLID = 0,
                        LINE_STYLE_DOTTED,
                } LINE_STYLE;
Draw a rectangle: In the image buffer, draw a rectangle from (Xstart, Ystart) to (Xend, Yend), you can choose the color, the width of the line, and whether to fill the inside of the rectangle.
void Paint_DrawRectangle(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD Color, DOT_PIXEL Line_width,  DRAW_FILL Draw_Fill)
Parameters:
        Xstart: the starting X coordinate of the rectangle
        Ystart: indicates the Y starting point of the rectangle
        Xend: X terminus of the rectangle
        Yend: specifies the y-end coordinate of the rectangle
        Color: fill Color
        Line_width: The width of the four sides of a rectangle. Default eight widths are provided
        typedef enum {
                DOT_PIXEL_1X1  = 1,	        // 1 x 1
                DOT_PIXEL_2X2  , 		// 2 X 2
                DOT_PIXEL_3X3  ,		// 3 X 3
                DOT_PIXEL_4X4  ,		// 4 X 4
                DOT_PIXEL_5X5  , 		// 5 X 5
                DOT_PIXEL_6X6  , 		// 6 X 6
                DOT_PIXEL_7X7  , 		// 7 X 7
                DOT_PIXEL_8X8  , 		// 8 X 8
        } DOT_PIXEL;
        Draw_Fill: Fill, whether to fill the inside of the rectangle
        typedef enum {
                DRAW_FILL_EMPTY = 0,
                DRAW_FILL_FULL,
        } DRAW_FILL;
Draw circle: In the image buffer, draw a circle of Radius with (X_Center Y_Center) as the center. You can choose the color, the width of the line, and whether to fill the inside of the circle.
void Paint_DrawCircle(UWORD X_Center, UWORD Y_Center, UWORD Radius, UWORD Color, DOT_PIXEL Line_width,  DRAW_FILL Draw_Fill)
Parameters:
        X_Center: the x-coordinate of the center of a circle
        Y_Center: Y coordinate of the center of a circle
        Radius: indicates the Radius of a circle
        Color: fill Color
        Line_width: The width of the arc, with a default of 8 widths
        typedef enum {
                DOT_PIXEL_1X1  = 1,	        // 1 x 1
                DOT_PIXEL_2X2  , 		// 2 X 2
                DOT_PIXEL_3X3  ,		// 3 X 3
                DOT_PIXEL_4X4  ,		// 4 X 4
                DOT_PIXEL_5X5  , 		// 5 X 5
                DOT_PIXEL_6X6  , 		// 6 X 6
                DOT_PIXEL_7X7  , 		// 7 X 7
                DOT_PIXEL_8X8  , 		// 8 X 8
        } DOT_PIXEL;
        Draw_Fill: fill, whether to fill the inside of the circle
        typedef enum {
                DRAW_FILL_EMPTY = 0,
                DRAW_FILL_FULL,
        } DRAW_FILL;
Write Ascii character: In the image buffer, at (Xstart Ystart) as the left vertex, write an Ascii character, you can select Ascii visual character library, font foreground color, font background color.
void Paint_DrawChar(UWORD Xstart, UWORD Ystart, const char Ascii_Char, sFONT* Font, UWORD Color_Foreground,  UWORD Color_Background)
Parameters:
        Xstart: the x-coordinate of the left vertex of a character
        Ystart: the Y coordinate of the font's left vertex
        Ascii_Char: indicates the Ascii character
        Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
                Font8: 5*8 font
                Font12: 7*12 font
                Font16: 11*16 font
                Font20: 14*20 font
                Font24: 17*24 font
        Color_Foreground: Font color
        Color_Background: indicates the background color
Write English string: In the image buffer, use (Xstart Ystart) as the left vertex, write a string of English characters, can choose Ascii visual character library, font foreground color, font background color.
void Paint_DrawString_EN(UWORD Xstart, UWORD Ystart, const char * pString, sFONT* Font, UWORD Color_Foreground,  UWORD Color_Background)
Parameters:
        Xstart: the x-coordinate of the left vertex of a character
        Ystart: the Y coordinate of the font's left vertex
        PString: string, string is a pointer
        Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
                Font8: 5*8 font
                Font12: 7*12 font
                Font16: 11*16 font
                Font20: 14*20 font
                Font24: 17*24 font
        Color_Foreground: Font color
        Color_Background: indicates the background color
Write Chinese string: in the image buffer, use (Xstart Ystart) as the left vertex, write a string of Chinese characters, you can choose GB2312 encoding character font, font foreground color, font background color.
void Paint_DrawString_CN(UWORD Xstart, UWORD Ystart, const char * pString, cFONT* font, UWORD Color_Foreground,  UWORD Color_Background)
Parameters:
        Xstart: the x-coordinate of the left vertex of a character
        Ystart: the Y coordinate of the font's left vertex
        PString: string, string is a pointer
        Font: GB2312 encoding character Font library, in the Fonts folder provides the following Fonts:
                Font12CN: ASCII font 11*21, Chinese font 16*21
                Font24CN: ASCII font24 *41, Chinese font 32*41
                Color_Foreground: Font color
                Color_Background: indicates the background color
Write numbers: In the image buffer,use (Xstart Ystart) as the left vertex, write a string of numbers, you can choose Ascii visual character library, font foreground color, font background color.
void Paint_DrawNum(UWORD Xpoint, UWORD Ypoint, double Nummber, sFONT* Font, UWORD Digit, UWORD Color_Foreground,   UWORD Color_Background)
Parameters:
        Xpoint: the x-coordinate of the left vertex of a character
        Ypoint: the Y coordinate of the left vertex of the font
        Nummber: indicates the number displayed, which can be a decimal
        Digit: It's a decimal number
        Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
                Font8: 5*8 font
                Font12: 7*12 font
                Font16: 11*16 font
                Font20: 14*20 font
                Font24: 17*24 font
        Color_Foreground: Font color
        Color_Background: indicates the background color
Write numbers with decimals: at (Xstart Ystart) as the left vertex, write a string of numbers with decimals, you can choose Ascii code visual character font, font foreground color, font background color
void Paint_DrawFloatNum(UWORD Xpoint, UWORD Ypoint, double Nummber, UBYTE Decimal_Point, sFONT* Font, UWORD Color_Foreground, UWORD Color_Background);
parameter:
         Xstart: the X coordinate of the left vertex of the character
         Ystart: Y coordinate of the left vertex of the font
         Nummber: the displayed number, which is saved in double type here
         Decimal_Point: Displays the number of digits after the decimal point
         Font: Ascii code visual character font library, the following fonts are provided in the Fonts folder:
                Font8: 5*8 font
                Font12: 7*12 font
                Font16: 11*16 font
                Font20: 14*20 font
                Font24: 17*24 font
        Color_Foreground: font color
        Color_Background: background color
Display time: in the image buffer,use (Xstart Ystart) as the left vertex, display time,you can choose Ascii visual character font, font foreground color, font background color.
void Paint_DrawTime(UWORD Xstart, UWORD Ystart, PAINT_TIME *pTime, sFONT* Font, UWORD Color_Background,  UWORD Color_Foreground)
Parameters:
        Xstart: the x-coordinate of the left vertex of a character
        Ystart: the Y coordinate of the font's left vertex
        PTime: display time, here defined a good time structure, as long as the hour, minute and second bits of data to the parameter;
        Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
                Font8: 5*8 font
                Font12: 7*12 font
                Font16: 11*16 font
                Font20: 14*20 font
                Font24: 17*24 font
        Color_Foreground: Font color
        Color_Background: indicates the background color
Display image: at (Xstart Ystart) as the left vertex, display an image whose width is W_Image and height is H_Image;
void Paint_DrawImage(const unsigned char *image, UWORD xStart, UWORD yStart, UWORD W_Image, UWORD H_Image)
parameter:
       image: image address, pointing to the image information you want to display
       Xstart: the X coordinate of the left vertex of the character
       Ystart: Y coordinate of the left vertex of the font
       W_Image: Image width
       H_Image: Image height
Demo Description
Document Introduction
Take Arduino UNO controlling a 1.54-inch LCD as an example, open the Arduino\LCD_1inch54 directory:
LCD arduino ide codeDescription1.png
Of which:
LCD_1inch54.ino: open with Arduino IDE;
LCD_Driver.cpp(.h): is the driver of the LCD screen;
DEV_Config.cpp(.h): It is the hardware interface definition, which encapsulates the read and write pin levels, SPI transmission data, and pin initialization;
font8.cpp, font12.cpp, font16.cpp, font20.cpp, font24.cpp, font24CN.cpp, fonts.h: fonts for characters of different sizes;
image.cpp(.h): is the image data, which can convert any BMP image into a 16-bit true color image array through Img2Lcd (downloadable in the development data).
The demo is divided into bottom-layer hardware interface, middle-layer LCD screen driver, and upper-layer application.

Underlying Hardware Interface
The hardware interface is defined in the two files DEV_Config.cpp(.h), and functions such as read and write pin level, delay, and SPI transmission are encapsulated.

write pin level
void DEV_Digital_Write(int pin, int value)
The first parameter is the pin, and the second is the high and low levels.

Read pin level
int DEV_Digital_Read(int pin)
The parameter is the pin, and the return value is the level of the read pin.

Delay
DEV_Delay_ms(unsigned int delaytime)
millisecond level delay.

SPI output data
DEV_SPI_WRITE(unsigned char data)
The parameter is char type, occupying 8 bits.

Upper Application
For the screen, if you need to draw pictures, display Chinese and English characters, display pictures, etc., you can use the upper application to do, and we provide some basic functions here about some graphics processing in the directory GUI_Paint.c(.h)
Note: Because of the size of the internal RAM of STM32 and Arduino, the GUI is directly written to the RAM of the LCD.
LCD arduino ide codeDescription GUI.png
The fonts used by the GUI all depend on the font*.cpp(h) files under the same file
LCD arduino ide codeDescription font.png

New Image Properties: Create a new image property, this property includes the image buffer name, width, height, flip Angle, color.
void Paint_NewImage(UWORD Width, UWORD Height, UWORD Rotate, UWORD Color)
Parameters:
    Width: image buffer Width;
    Height: the Height of the image buffer;
    Rotate: Indicates the rotation Angle of an image
    Color: the initial Color of the image;
Set the clear screen function, usually call the clear function of LCD directly.
void Paint_SetClearFuntion(void (*Clear)(UWORD));
parameter:
    Clear: Pointer to the clear screen function used to quickly clear the screen to a certain color;
Set the drawing pixel function.
void Paint_SetDisplayFuntion(void (*Display)(UWORD,UWORD,UWORD));
parameter:
    Display: Pointer to the pixel drawing function, which is used to write data to the specified location in the internal RAM of the LCD;
Select image buffer: the purpose of the selection is that you can create multiple image attributes, an image buffer can exist multiple, and you can select each image you create.
void Paint_SelectImage(UBYTE *image)
Parameters:
    Image: the name of the image cache, which is actually a pointer to the first address of the image buffer
Image Rotation: Set the selected image rotation Angle, preferably after Paint_SelectImage(), you can choose to rotate 0, 90, 180, 270.
Rotation-lcd.png

void Paint_SetRotate(UWORD Rotate)
Parameters:
    Rotate: ROTATE_0, ROTATE_90, ROTATE_180, and ROTATE_270 correspond to 0, 90, 180, and 270 degrees respectively;
Image mirror flip: Set the mirror flip of the selected image. You can choose no mirror, horizontal mirror, vertical mirror, or image center mirror.
void Paint_SetMirroring(UBYTE mirror)
Parameters:
    Mirror: indicates the image mirroring mode. MIRROR_NONE, MIRROR_HORIZONTAL, MIRROR_VERTICAL, MIRROR_ORIGIN correspond to no mirror, horizontal mirror, vertical mirror, and about image center mirror respectively.
Set points of display position and color in the buffer: here is the core GUI function, processing points display position and color in the buffer.
void Paint_SetPixel(UWORD Xpoint, UWORD Ypoint, UWORD Color)
Parameters:
    Xpoint: the X position of a point in the image buffer
    Ypoint: Y position of a point in the image buffer
    Color: indicates the Color of the dot
Image buffer fill color: Fills the image buffer with a color, usually used to flash the screen into blank.
void Paint_ClearWindows(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD Color)
Parameters:
    Xstart: the x-starting coordinate of the window
    Ystart: indicates the Y starting point of the window
    Xend: the x-end coordinate of the window
    Yend: indicates the y-end coordinate of the window
    Color: fill Color
Draw points: In the image buffer, draw points on (Xpoint, Ypoint), you can choose the color, the size of the point, and the style of the point.
void Paint_DrawPoint(UWORD Xpoint, UWORD Ypoint, UWORD Color, DOT_PIXEL Dot_Pixel, DOT_STYLE Dot_Style)
Parameters:
    Xpoint: indicates the X coordinate of a point
    Ypoint: indicates the Y coordinate of a point
    Color: fill Color
    Dot_Pixel: The size of the dot, providing a default of eight size points
        typedef enum {
                DOT_PIXEL_1X1  = 1,	        // 1 x 1
                DOT_PIXEL_2X2  , 		// 2 X 2
                DOT_PIXEL_3X3  , 	 	// 3 X 3
                DOT_PIXEL_4X4  , 	 	// 4 X 4
                DOT_PIXEL_5X5  , 		// 5 X 5
                DOT_PIXEL_6X6  , 		// 6 X 6
                DOT_PIXEL_7X7  , 		// 7 X 7
                DOT_PIXEL_8X8  , 		// 8 X 8
        } DOT_PIXEL;
    Dot_Style: the size of a point that expands from the center of the point or from the bottom left corner of the point to the right and up
        typedef enum {
                DOT_FILL_AROUND  = 1,
                DOT_FILL_RIGHTUP,
        } DOT_STYLE;
Line drawing: In the image buffer, line from (Xstart, Ystart) to (Xend, Yend), you can choose the color, line width, and line style.
void Paint_DrawLine(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD Color, LINE_STYLE Line_Style ,  LINE_STYLE Line_Style)
Parameters:
        Xstart: the x-starting coordinate of a line
        Ystart: indicates the Y starting point of a line
        Xend: x-terminus of a line
        Yend: the y-end coordinate of a line
        Color: fill Color
        Line_width: The width of the line, which provides a default of eight widths
                typedef enum {
                        DOT_PIXEL_1X1  = 1,	        // 1 x 1
                        DOT_PIXEL_2X2  , 		// 2 X 2
                        DOT_PIXEL_3X3  ,		// 3 X 3
                        DOT_PIXEL_4X4  ,		// 4 X 4
                        DOT_PIXEL_5X5  , 		// 5 X 5
                        DOT_PIXEL_6X6  , 		// 6 X 6
                        DOT_PIXEL_7X7  , 		// 7 X 7
                        DOT_PIXEL_8X8  , 		// 8 X 8
                    } DOT_PIXEL;
        Line_Style: line style. Select whether the lines are joined in a straight or dashed way
                typedef enum {
                        LINE_STYLE_SOLID = 0,
                        LINE_STYLE_DOTTED,
                } LINE_STYLE;
Draw a rectangle: In the image buffer, draw a rectangle from (Xstart, Ystart) to (Xend, Yend), you can choose the color, the width of the line, and whether to fill the inside of the rectangle.
void Paint_DrawRectangle(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD Color, DOT_PIXEL Line_width,  DRAW_FILL Draw_Fill)
Parameters:
        Xstart: the starting X coordinate of the rectangle
        Ystart: indicates the Y starting point of the rectangle
        Xend: X terminus of the rectangle
        Yend: specifies the y-end coordinate of the rectangle
        Color: fill Color
        Line_width: The width of the four sides of a rectangle. Default eight widths are provided
        typedef enum {
                DOT_PIXEL_1X1  = 1,	        // 1 x 1
                DOT_PIXEL_2X2  , 		// 2 X 2
                DOT_PIXEL_3X3  ,		// 3 X 3
                DOT_PIXEL_4X4  ,		// 4 X 4
                DOT_PIXEL_5X5  , 		// 5 X 5
                DOT_PIXEL_6X6  , 		// 6 X 6
                DOT_PIXEL_7X7  , 		// 7 X 7
                DOT_PIXEL_8X8  , 		// 8 X 8
        } DOT_PIXEL;
        Draw_Fill: Fill, whether to fill the inside of the rectangle
        typedef enum {
                DRAW_FILL_EMPTY = 0,
                DRAW_FILL_FULL,
        } DRAW_FILL;
Draw circle: In the image buffer, draw a circle of Radius with (X_Center Y_Center) as the center. You can choose the color, the width of the line, and whether to fill the inside of the circle.
void Paint_DrawCircle(UWORD X_Center, UWORD Y_Center, UWORD Radius, UWORD Color, DOT_PIXEL Line_width,  DRAW_FILL Draw_Fill)
Parameters:
        X_Center: the x-coordinate of the center of a circle
        Y_Center: Y coordinate of the center of a circle
        Radius: indicates the Radius of a circle
        Color: fill Color
        Line_width: The width of the arc, with a default of 8 widths
        typedef enum {
                DOT_PIXEL_1X1  = 1,	        // 1 x 1
                DOT_PIXEL_2X2  , 		// 2 X 2
                DOT_PIXEL_3X3  ,		// 3 X 3
                DOT_PIXEL_4X4  ,		// 4 X 4
                DOT_PIXEL_5X5  , 		// 5 X 5
                DOT_PIXEL_6X6  , 		// 6 X 6
                DOT_PIXEL_7X7  , 		// 7 X 7
                DOT_PIXEL_8X8  , 		// 8 X 8
        } DOT_PIXEL;
        Draw_Fill: fill, whether to fill the inside of the circle
        typedef enum {
                DRAW_FILL_EMPTY = 0,
                DRAW_FILL_FULL,
        } DRAW_FILL;
Write Ascii character: In the image buffer, at (Xstart Ystart) as the left vertex, write an Ascii character, you can select Ascii visual character library, font foreground color, font background color.
void Paint_DrawChar(UWORD Xstart, UWORD Ystart, const char Ascii_Char, sFONT* Font, UWORD Color_Foreground,  UWORD Color_Background)
Parameters:
        Xstart: the x-coordinate of the left vertex of a character
        Ystart: the Y coordinate of the font's left vertex
        Ascii_Char: indicates the Ascii character
        Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
                Font8: 5*8 font
                Font12: 7*12 font
                Font16: 11*16 font
                Font20: 14*20 font
                Font24: 17*24 font
        Color_Foreground: Font color
        Color_Background: indicates the background color
Write English string: In the image buffer, use (Xstart Ystart) as the left vertex, write a string of English characters, can choose Ascii visual character library, font foreground color, font background color.
void Paint_DrawString_EN(UWORD Xstart, UWORD Ystart, const char * pString, sFONT* Font, UWORD Color_Foreground,  UWORD Color_Background)
Parameters:
        Xstart: the x-coordinate of the left vertex of a character
        Ystart: the Y coordinate of the font's left vertex
        PString: string, string is a pointer
        Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
                Font8: 5*8 font
                Font12: 7*12 font
                Font16: 11*16 font
                Font20: 14*20 font
                Font24: 17*24 font
        Color_Foreground: Font color
        Color_Background: indicates the background color
Write Chinese string: in the image buffer, use (Xstart Ystart) as the left vertex, and write a string of Chinese characters, you can choose GB2312 encoding character font, font foreground color, and font background color.
void Paint_DrawString_CN(UWORD Xstart, UWORD Ystart, const char * pString, cFONT* font, UWORD Color_Foreground,  UWORD Color_Background)
Parameters:
        Xstart: the x-coordinate of the left vertex of a character
        Ystart: the Y coordinate of the font's left vertex
        PString: string, string is a pointer
        Font: GB2312 encoding character Font library, in the Fonts folder provides the following Fonts:
                Font12CN: ASCII font 11*21, Chinese font 16*21
                Font24CN: ASCII font24 *41, Chinese font 32*41
                Color_Foreground: Font color
                Color_Background: indicates the background color
Write numbers: In the image buffer, use (Xstart Ystart) as the left vertex, and write a string of numbers, you can choose Ascii visual character library, font foreground color, or font background color.
void Paint_DrawNum(UWORD Xpoint, UWORD Ypoint, double Nummber, sFONT* Font, UWORD Digit, UWORD Color_Foreground,   UWORD Color_Background)
Parameters:
        Xpoint: the x-coordinate of the left vertex of a character
        Ypoint: the Y coordinate of the left vertex of the font
        Nummber: indicates the number displayed, which can be a decimal
        Digit: It's a decimal number
        Font: Ascii visual character library, in the Fonts folder provides the following Fonts:
                Font8: 5*8 font
                Font12: 7*12 font
                Font16: 11*16 font
                Font20: 14*20 font
                Font24: 17*24 font
        Color_Foreground: Font color
        Color_Background: indicates the background color
Write numbers with decimals: at (Xstart Ystart) as the left vertex, write a string of numbers with decimals, you can choose Ascii code visual character font, font foreground color, font background color
void Paint_DrawFloatNum(UWORD Xpoint, UWORD Ypoint, double Nummber, UBYTE Decimal_Point, sFONT* Font, UWORD Color_Foreground, UWORD Color_Background);
parameter:
         Xstart: the X coordinate of the left vertex of the character
         Ystart: Y coordinate of the left vertex of the font
         Nummber: the displayed number, which is saved in double type here
         Decimal_Point: Displays the number of digits after the decimal point
         Font: Ascii code visual character font library, the following fonts are provided in the Fonts folder:
                Font8: 5*8 font
                Font12: 7*12 font
                Font16: 11*16 font
                Font20: 14*20 font
                Font24: 17*24 font
        Color_Foreground: font color
        Color_Background: background color
Display time: in the image buffer,use (Xstart Ystart) as the left vertex, display time,you can choose Ascii visual character font, font foreground color, font background color.
void Paint_DrawTime(UWORD Xstart, UWORD Ystart, PAINT_TIME *pTime, sFONT* Font, UWORD Color_Background,  UWORD Color_Foreground)
Parameters:
        Xstart: the x-coordinate of the left vertex of a character
        Ystart: the Y coordinate of the font's left vertex
        PTime: display time, here defined as a good time structure, as long as the hour, minute and second bits of data to the parameter;
        Font: Ascii visual character library, in the Fonts folder, provides the following Fonts:
                Font8: 5*8 font
                Font12: 7*12 font
                Font16: 11*16 font
                Font20: 14*20 font
                Font24: 17*24 font
        Color_Foreground: Font color
        Color_Background: indicates the background color
Display image: at (Xstart Ystart) as the left vertex, display an image whose width is W_Image and height is H_Image;
void Paint_DrawImage(const unsigned char *image, UWORD xStart, UWORD yStart, UWORD W_Image, UWORD H_Image)
parameter:
       image: image address, pointing to the image information you want to display
       Xstart: the X coordinate of the left vertex of the character
       Ystart: Y coordinate of the left vertex of the font
       W_Image: Image width
       H_Image: Image height
Resource
Document
Schematic
ST7789V2 datasheet
2D Drawing
3D Drawing
Demo
Demo example
Software
lcd
Image2Lcd
Image Extraction
FAQ
Question: What is the maximum power consumption of 1.69inch LCD Module?
 Answer:
3.3V 90mA



Question: The maximum brightness of 1.69inch LCD Module is?
 Answer:
3.3V 500cd/㎡



Support



Technical Support

If you need technical support or have any feedback/review, please click the Submit Now button to submit a ticket, Our support team will check and reply to you within 1 to 2 working days. Please be patient as we make every effort to help you to resolve the issue.
Working Time: 9 AM - 6 PM GMT+8 (Monday to Friday)

Submit Now


Overview
Specifications
Module & Control Chip
Communication Protocol
Raspberry Pi
Hardware Connection
Enable SPI Interface
Running C Demo
Run Python Demo
FBCP Porting
Download Drivers
Method 1: Use a script (recommended)
Method 2: Manual Configuration
Environment Configuration
Compile and Run
Set up to Start Automatically
Set the Display Resolution
STM32
Hardware Connection
Run the Demo
Demo Description
Underlying Hardware Interface
Upper Application
Arduino
IDE Installation
Hardware Connection
Run the Demo
Demo Description
Document Introduction
Underlying Hardware Interface
Upper Application
Demo Description
Document Introduction
Underlying Hardware Interface
Upper Application
Resource
Document
Demo
Software
FAQ
Support
To Top
Login / Create Account and then here is context about what all this will be dong SCIENCE OLYMPIAD / DIVISION C

ELECTRIC
VEHICLE
＋
Engineering for repeatable precision.

A PARTNERSHIP PITCH TO RoviSys
Harjas [Last name] · [Team / School]
DESIGNED IN SOLIDWORKS

HERO VEHICLE RENDER
3/4 VIEW • DARK STUDIO BACKGROUND

01 / 16

ROVISYS / SCIENCE OLYMPIAD
01 / THE OPPORTUNITY

A real engineering problem. A measurable result.
Science Olympiad turns classroom STEM into a hands-on engineering competition.

15 STUDENTS

4 STEM DOMAINS

3 LEVELS

Teams compete across approximately 23 events.

Engineering, physical, life and earth science.

Regional → State → National.

One event is especially engineeringintensive:

＋
TEAM / COMPETITION PHOTO
SCIENCE OLYMPIAD TEAM IN ACTION

ELECTRIC VEHICLE • 2027

02 / 16

ELECTRIC
VEHICLE

ROVISYS / SCIENCE OLYMPIAD
01 / THE OPPORTUNITY

The event: autonomous electric vehicle
Build, program and test a vehicle that completes a changing task without remote control.

• One vehicle, built by a team of up to two
• Electrical power only: up to eight AA batteries
• Fully autonomous: no remote control or tether
• Eight minutes to adjust, repair and run
• Two scored runs; the lower score counts

＋

COMPETITION COURSE PHOTO
TRACK / BOTTLE / TARGET POINT

THE TASK CHANGES EVERY SEASON.

ELECTRIC VEHICLE • 2027

03 / 16

ROVISYS / SCIENCE OLYMPIAD
01 / THE CHALLENGE

One run. Three precision problems.
The vehicle must complete the sequence, then finish close to the target at the right time.

01 ALIGN
Place the rear Measurement Point within about 1 cm of Start.

＋

02 COMPLETE
Drive forward and push the bottle past the line.

03 STOP
RUN SEQUENCE DIAGRAM

Reverse and stop close to Target Point at 10–20 seconds.

START → PUSH BOTTLE → REVERSE → TARGET

Pencil tap starts the autonomous run.

ELECTRIC VEHICLE • 2027

04 / 16

ROVISYS / SCIENCE OLYMPIAD
01 / THE CHALLENGE

Precision is the scoring strategy
Low score wins. Distance, time, bonuses and penalties all matter.

2 pts / cm

1 pt / cm

0.5 pt / sec

−20 pts

VEHICLE DISTANCE

BOTTLE DISTANCE

TIME DIFFERENCE

BOTTLE PAST LINE

RUN SCORE

ADDITIONAL BONUS

100 + distance + time + bonuses + penalties

−1.5 points per centimeter the pusher opening is under 35 cm.

The better of two runs counts.

Every centimeter and every second costs points. Repeatability matters.

ELECTRIC VEHICLE • 2027

05 / 16

ROVISYS / SCIENCE OLYMPIAD
01 / THE CHALLENGE

The 2027 task raises the bar
The vehicle must manage both forward placement and a controlled reverse stop.

＋

＋

PREVIOUS SEASON TASK

2027 TASK ILLUSTRATION

DRIVE BETWEEN TWO CANS • STOP

PUSH BOTTLE PAST LINE • REVERSE • STOP

PREVIOUS SEASON

2027

More to get right in a single run.

ELECTRIC VEHICLE • 2027

06 / 16

ROVISYS / SCIENCE OLYMPIAD
01 / DESIGN CONSTRAINTS

Rules define the design envelope
The engineering challenge is to deliver precision inside strict physical and electrical limits.

POWER

PROHIBITED

Maximum 8 AA batteries • 1.2–1.5 V each when fully charged

No lithium or lead batteries • no lasers • no cameras

ENVELOPE

PUSHER

Maximum 80 cm long × 35 cm wide

Rigid front pusher, rounded edges, no moving parts

MEASUREMENT

AUTONOMY

Rear-most point, 1 cm or less above the track

No remote control and no AI during event time

ELECTRIC VEHICLE • 2027

07 / 16

ROVISYS / SCIENCE OLYMPIAD
02 / ENGINEERING DECISIONS

Why independent left/right drive?
The drivetrain architecture is a direct response to the need for accurate stopping and correction.

＋

＋

＋

2WD CONCEPT

4WD / ONE MOTOR

4WD / MOTOR PER SIDE

SIMPLE • LESS STABLE

STABLE • CAN DRIFT

INDEPENDENT CONTROL

2WD

4WD / ONE MOTOR

4WD / TWO MOTORS

One slip can compromise the run.

A worn pinion or bad wheel affects the whole drive.

Each side is controlled independently; drift can be
corrected.

ELECTRIC VEHICLE • 2027

08 / 16

ROVISYS / SCIENCE OLYMPIAD
03 / OUR VEHICLE

A compact platform built around control
4WD • one motor per side • parallel drivetrain connected by timing belts

213 × 200 × 35
CHASSIS (MM)

Ø45 mm

＋

WHEELS

4WD
DRIVE LAYOUT

VEHICLE CAD RENDER

Well inside the 80 × 35 cm event limit.

3/4 VIEW • ADD ANNOTATION CALLOUTS

Previous results: 6th at Regionals • 11th at State
VEHICLE CAD • DESIGNED IN SOLIDWORKS

ELECTRIC VEHICLE • 2027

09 / 16

ROVISYS / SCIENCE OLYMPIAD
03 / OUR VEHICLE

Drivetrain: power to the wheels
Each side is controlled on its own, so a slip on one side can be corrected rather than carried through the run.

＋

1100 RPM

22.5:1

MOTOR OUTPUT

DARTBOX RATIO

4.2 kgf·cm

3.5 A

STALL TORQUE

STALL CURRENT

DRIVETRAIN CAD CLOSE-UP
MOTOR → GEARBOX → PULLEYS → BELTS → WHEELS

POWER

TRANSMISSION

SPEED

8 × AA • nominal 12 V

25T → GT2 belt → 27T

≈ 2.4 m/s theoretical no-load

ELECTRIC VEHICLE • 2027

10 / 16

ROVISYS / SCIENCE OLYMPIAD
03 / OUR VEHICLE

Know where the vehicle is
Wheel feedback measures travel; inertial sensing helps estimate heading and motion.

AS5600 • WHEEL ENCODERS
12-bit magnetic encoder • 4096 counts/revolution
Measures wheel speed and distance for closed-loop control
≈ 0.035 mm travel per count (wheel-shaft mount)

＋
WITMOTION WT901 • IMU
9-axis accelerometer, gyroscope and magnetometer
On-board Kalman filtering up to 200 Hz
Heading uses gyro; motors can disturb magnetometer

SENSOR PLACEMENT DIAGRAM
AS5600 ON EACH SIDE • WT901 IMU

ELECTRIC VEHICLE • 2027

11 / 16

ROVISYS / SCIENCE OLYMPIAD
03 / OUR VEHICLE

The control system closes the loop
Sensor fusion estimates motion; filtering cleans the signal; PID control drives each side.

＋

ELECTRONICS ARCHITECTURE DIAGRAM
ENCODERS + IMU → RP2350 DUAL-CORE → WEKA 20A DUAL ESC → MOTORS

ESTIMATE

FILTER

CONTROL

Kalman filter fuses encoder and IMU data.

Low-pass / high-pass filtering and deadband
compensation.

PID motion control with one loop per side.

WEKA ESC: 20 A per channel • 7.5–30 V • braking • current limiting • thermal and low-voltage protection

ELECTRIC VEHICLE • 2027

12 / 16

ROVISYS / SCIENCE OLYMPIAD
03 / OUR VEHICLE

Structure: light, rigid and serviceable
A layered chassis combines carbon fiber, aluminum, acrylic isolation and custom printed parts.

ALUMINUM
Side and back plates use a Voronoi cutout pattern.

CARBON FIBER
Top and bottom plates.

＋

ACRYLIC + ALUMINUM
Internal liner for electrical isolation; connecting members add rigidity.

CUSTOM PARTS

EXPLODED CHASSIS RENDER

30A Shore molded wheels • PETG-CF printed components.

ELECTRIC VEHICLE • 2027

13 / 16

LABEL EACH MATERIAL LAYER

ROVISYS / SCIENCE OLYMPIAD
03 / OUR VEHICLE

Designed for repeatable setup
Fast alignment, clear status and tool-free service reduce friction between runs.

＋

＋

GIF / SCOPE ALIGNMENT

GIF / BATTERY INSTALLATION

SCOPE LOWERING AND SNAP-FIT ON MAGNETS

BATTERY HOLDER, CONNECTOR AND COVER

MAGNETIC SCOPE

PUSH-BUTTON START

1.69″ DISPLAY

8 × AA PACK

Tool-free alignment aid.

Triggered by required pencil tap.

Live vehicle status.

Quick removal for inspection.

ELECTRIC VEHICLE • 2027

14 / 16

ROVISYS / SCIENCE OLYMPIAD
04 / THE PARTNERSHIP

A transparent build budget
Current team bill of materials: approximately $571.

Structure

$170.25

Aluminum, carbon fiber, acrylic, PETG-CF, vinyl

Drive & motion

$163.66

Gearmotors, ESC, belts, bearings, wheel resin

＋
Electronics & sensing

$151.19

RP2350, IMU, encoders, display, wiring, connectors,
battery holder

Hardware

$55.94

Screws, heated inserts, standoffs

Alignment

$30.00

Scope

BUDGET BREAKDOWN GRAPHIC

ELECTRIC VEHICLE • 2027

15 / 16

DONUT / BAR CHART

Source: team BOM. Some hardware comes in bulk packs.

04 / THE PARTNERSHIP

Help us engineer
the next run.
We are looking for a partner to support the next stage of
our Electric Vehicle build.

＋

THE PARTNERSHIP

• RoviSys logo placement on the vehicle top plate
• Recognition on team materials
• Updates on competition results

TOP-VIEW VEHICLE RENDER
SHOW PROPOSED RoviSys LOGO PLACEMENT

THE ASK / [ADD SPECIFIC REQUEST]

THANK YOU / QUESTIONS?

16 / 16

