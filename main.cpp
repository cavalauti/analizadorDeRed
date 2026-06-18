#include <Arduino.h>
#include <TFT_eSPI.h>

// --- MAPEO DE PINES ---
#define YP 12  // LCD_WR
#define XM 27  // LCD_D0
#define YM 26  // LCD_D1
#define XP 2   // LCD_RS / DC

TFT_eSPI tft = TFT_eSPI();

// Historiales para el filtro de estabilidad
int histX[3] = {0, 0, 0};
int histY[3] = {0, 0, 0};
bool yaRegistroElToque = false;

// Control de tiempo para evitar rebotes
unsigned long ultimoToqueTiempo = 0;
const unsigned long MULTI_TOUCH_SHIELD = 350; 

// --- COORDENADAS DE LOS BOTONES ---
const int btnW = 70;
const int btnH = 35;
const int colX[3] = {40, 125, 210};
const int filaY[4] = {60, 105, 150, 195};

void actualizarVisor(String texto) {
    tft.fillRect(21, 11, 278, 38, TFT_DARKGREY);
    tft.setTextColor(TFT_WHITE, TFT_DARKGREY);
    tft.setTextFont(4);
    tft.setTextSize(1);
    
    tft.setCursor(35, 18);
    tft.print("Tocado: " + texto);
}

void dibujarInterfaz() {
    tft.fillScreen(TFT_BLACK);

    // 1. Visor
    tft.drawRoundRect(20, 10, 280, 40, 5, TFT_WHITE);
    actualizarVisor("Ninguno");

    // 2. Botones 1 al 9
    tft.setTextFont(4);
    tft.setTextSize(1);
    tft.setTextColor(TFT_BLACK, TFT_LIGHTGREY); 

    char num = '1';
    for (int f = 0; f < 3; f++) {
        for (int c = 0; c < 3; c++) {
            tft.fillRoundRect(colX[c], filaY[f], btnW, btnH, 4, TFT_LIGHTGREY);
            tft.setCursor(colX[c] + 28, filaY[f] + 5);
            tft.print(num++);
        }
    }

    // 3. Botón 0 largo
    tft.fillRoundRect(colX[0], filaY[3], 240, btnH, 4, TFT_LIGHTGREY);
    tft.setCursor(colX[1] + 28, filaY[3] + 5);
    tft.print("0");
}

void procesarToqueEnPixel(int px, int py) {
    char botonPresionado = ' ';
    int columna = -1;
    int fila = -1;

    // --- 🎯 DETECCIÓN POR REGIONES CONTINUAS (Elimina zonas muertas) ---
    // División horizontal (Eje X)
    if (px < 115) {
        columna = 0; // Columna del 1, 4, 7
    } else if (px < 195) {
        columna = 1; // Columna del 2, 5, 8
    } else {
        columna = 2; // Columna del 3, 6, 9
    }

    // División vertical (Eje Y) - Absorbe la compresión del botón 3
    if (py < 100) {
        fila = 0;    // Fila del 1, 2, 3 (Ahora acepta desde Y=0 hasta 100)
    } else if (py < 145) {
        fila = 1;    // Fila del 4, 5, 6
    } else if (py < 190) {
        fila = 2;    // Fila del 7, 8, 9
    } else {
        fila = 3;    // Fila del 0
    }
    // -----------------------------------------------------------------

    // Validación de seguridad para no registrar toques extremadamente fuera de los bordes
    if (px < 15 || px > 305 || py > 235) {
        Serial.println("-> Toque descartado por estar en los límites externos físicos.");
        return;
    }

    // Asignación final del botón
    if (fila >= 0 && fila <= 2) {
        int indice = fila * 3 + columna + 1;
        botonPresionado = '0' + indice;
    } else if (fila == 3) {
        botonPresionado = '0';
    }

    if (botonPresionado != ' ') {
        Serial.print("-> ¡BOTÓN DETECTADO!: "); Serial.println(botonPresionado);
        actualizarVisor(String(botonPresionado));
    }
}

void setup() {
    Serial.begin(115200);
    analogSetWidth(12);

    pinMode(13, OUTPUT);
    digitalWrite(13, HIGH);

    tft.init();
    tft.setRotation(1); 
    dibujarInterfaz();

    Serial.println("\n=== Calculadora con Hitboxes Inteligentes Iniciada ===");
}

void loop() {
    // 1. LECTURA DEL EJE X DE LA PANTALLA (Desde YM)
    pinMode(XP, OUTPUT); digitalWrite(XP, HIGH);
    pinMode(XM, OUTPUT); digitalWrite(XM, LOW);
    pinMode(YP, INPUT);  pinMode(YM, INPUT);
    delay(6); 
    int x = (analogRead(YM) + analogRead(YM) + analogRead(YM)) / 3; 

    // 2. LECTURA DEL EJE Y DE LA PANTALLA
    pinMode(YP, OUTPUT); digitalWrite(YP, HIGH);
    pinMode(YM, OUTPUT); digitalWrite(YM, LOW);
    pinMode(XP, INPUT);  pinMode(XM, INPUT);
    delay(6);
    int y = (analogRead(XP) + analogRead(XP) + analogRead(XP)) / 3; 

    // 3. RESTAURACIÓN DEL BUS GRÁFICO
    pinMode(XM, OUTPUT); pinMode(YP, OUTPUT);
    pinMode(XP, OUTPUT); pinMode(YM, OUTPUT);
    digitalWrite(YP, HIGH); 

    // 4. DESPLAZAR HISTORIAL
    for (int i = 0; i < 2; i++) {
        histX[i] = histX[i + 1];
        histY[i] = histY[i + 1];
    }
    histX[2] = x;
    histY[2] = y;

    // 5. CALCULAR DELTAS
    int maxX = max(histX[0], max(histX[1], histX[2]));
    int minX = min(histX[0], min(histX[1], histX[2]));
    int deltaX = maxX - minX;

    int maxY = max(histY[0], max(histY[1], histY[2]));
    int minY = min(histY[0], min(histY[1], histY[2]));
    int deltaY = maxY - minY;

    // 6. EVALUACIÓN LÓGICA ANTI-FANTASMAS
    bool esSenalEstable = (deltaX < 75 && deltaY < 75);
    bool esReposoAbsoluto = (x >= 4050 || y < 400); 
    bool detectadoDedo = esSenalEstable && !esReposoAbsoluto;

    // 7. MÁQUINA DE ESTADOS
    if (detectadoDedo) {
        if (!yaRegistroElToque && (millis() - ultimoToqueTiempo > MULTI_TOUCH_SHIELD)) {
            
            // Decodificación matemática
            int pixelX = map(y, 3600, 460, 0, 320);
            int x_puro_y = x - (int)(0.42 * y);
            int pixelY = map(x_puro_y, 3150, 1820, 0, 240);

            Serial.printf("RAW -> X:%d Y:%d | Desacoplado -> Pixel X:%d Y:%d\n", x, y, pixelX, pixelY);
            
            procesarToqueEnPixel(pixelX, pixelY);
            
            yaRegistroElToque = true; 
            ultimoToqueTiempo = millis(); 
        }
    } else {
        yaRegistroElToque = false;
    }

    delay(10); 
}
