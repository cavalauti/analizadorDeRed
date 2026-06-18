#include <Arduino.h>
#include <TFT_eSPI.h>

// --- MAPEO DE PINES ---
#define YP 12  // LCD_WR
#define XM 27  // LCD_D0
#define YM 26  // LCD_D1
#define XP 2   // LCD_RS / DC

TFT_eSPI tft = TFT_eSPI();
bool colorAmarillo = false;

// Historiales para el filtro de estabilidad
int histX[3] = {0, 0, 0};
int histY[3] = {0, 0, 0};
bool yaRegistroElToque = false;

// CONTROL DE TIEMPO
unsigned long ultimoToqueTiempo = 0;
const unsigned long MULTI_TOUCH_SHIELD = 350; 

void actualizarPantalla() {
    uint16_t colorFondo = colorAmarillo ? TFT_YELLOW : TFT_BLUE;
    uint16_t colorTexto = colorAmarillo ? TFT_BLACK : TFT_WHITE;
    
    tft.fillScreen(colorFondo);
    tft.setTextColor(colorTexto, colorFondo);
    
    tft.setTextFont(4); 
    tft.setTextSize(1);
    
    tft.setCursor(50, 90);
    tft.print(colorAmarillo ? "MODO: AMARILLO" : "MODO: AZUL");

    tft.setTextFont(2);
    tft.setCursor(40, 140);
    tft.print("Filtro de Estabilidad Sensible");
}

void setup() {
    Serial.begin(115200);
    analogSetWidth(12);

    pinMode(13, OUTPUT);
    digitalWrite(13, HIGH);

    tft.init();
    tft.setRotation(1); 
    actualizarPantalla();

    Serial.println("\n=== Buscador de Estabilidad Sensible Iniciado ===");
}

void loop() {
    // 1. LECTURA DEL EJE X (Con triple lectura para suavizar toque suave)
    pinMode(XP, OUTPUT); digitalWrite(XP, HIGH);
    pinMode(XM, OUTPUT); digitalWrite(XM, LOW);
    pinMode(YP, INPUT);  pinMode(YM, INPUT);
    delay(6); 
    int x = (analogRead(YP) + analogRead(YP) + analogRead(YP)) / 3; // Promedio anti-ruido

    // 2. LECTURA DEL EJE Y
    pinMode(YP, OUTPUT); digitalWrite(YP, HIGH);
    pinMode(YM, OUTPUT); digitalWrite(YM, LOW);
    pinMode(XP, INPUT);  pinMode(XM, INPUT);
    delay(6);
    int y = (analogRead(XP) + analogRead(XP) + analogRead(XP)) / 3; // Promedio anti-ruido

    // 3. RESTAURACIÓN INMEDIATA DEL BUS GRÁFICO
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

    // 5. CALCULAR DELTAS (Paréntesis corregidos quirúrgicamente)
    int maxX = max(histX[0], max(histX[1], histX[2]));
    int minX = min(histX[0], min(histX[1], histX[2]));
    int deltaX = maxX - minX;

    int maxY = max(histY[0], max(histY[1], histY[2]));
    int minY = min(histY[0], min(histY[1], histY[2]));
    int deltaY = maxY - minY;

    // 6. EVALUACIÓN LÓGICA RECALIBRADA
    // Tolerancia a 55 para aceptar el "temblor" natural del toque suave
    bool esSenalEstable = (deltaX < 55 && deltaY < 55);
    
    // El descarte del reposo sigue firme
    bool esReposoAbsoluto = (x > 4040 && y < 40);

    bool detectadoDedo = esSenalEstable && !esReposoAbsoluto;

    // 7. MÁQUINA DE ESTADOS
    if (detectadoDedo) {
        if (!yaRegistroElToque && (millis() - ultimoToqueTiempo > MULTI_TOUCH_SHIELD)) {
            Serial.print("¡Toque Sensible Detectado! -> X: "); Serial.print(x);
            Serial.print(" | Y: "); Serial.println(y);
            
            colorAmarillo = !colorAmarillo;
            actualizarPantalla();
            
            yaRegistroElToque = true; 
            ultimoToqueTiempo = millis(); 
        }
    } else {
        yaRegistroElToque = false;
    }

    delay(10); 
}