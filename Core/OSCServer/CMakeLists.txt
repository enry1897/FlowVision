cmake_minimum_required(VERSION 3.16)
project(OSCGPIOController)

set(CMAKE_CXX_STANDARD 17)

# Trova i pacchetti necessari
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)
find_package(PkgConfig REQUIRED)
pkg_check_modules(LO REQUIRED lo)
pkg_check_modules(GPIOD REQUIRED libgpiod)

# Aggiungi includepath delle dipendenze
include_directories(
    ${LO_INCLUDE_DIRS}
    ${GPIOD_INCLUDE_DIRS}
)

# Source files
set(SOURCES
    src/main.cpp
    src/MainWindow.cpp
    src/GpioHandler.cpp
    src/OSCServer.cpp
)

set(HEADERS
    head/MainWindow.h
    head/GpioHandler.h
    head/OSCServer.h
)

# Crea eseguibile
add_executable(OSCGPIOController ${SOURCES} ${HEADERS})

# Link Qt e librerie esterne
target_link_libraries(OSCGPIOController
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    ${LO_LIBRARIES}
    ${GPIOD_LIBRARIES}
)
