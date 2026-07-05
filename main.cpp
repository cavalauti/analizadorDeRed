#include <Arduino.h>
#include <TFT_eSPI.h>
#include <WiFi.h>
#include <time.h>

// --- MAPEO DE PINES COMPARTIDOS (TOUCH Y VIDEO) ---
#define YP 12  // LCD_WR
#define XM 27  // LCD_D0
#define YM 26  // LCD_D1
#define XP 2   // LCD_RS / DC

// --- MAPEO DE PINES SENSORES ---
#define PIN_ZMPT 34
#define PIN_ACS  35

TFT_eSPI tft = TFT_eSPI();

// --- CONFIGURACIÓN WI-FI Y NTP ---
const char* ssid       = "Cotecal_LOJO-2g"; // Reemplaza con tu Wi-Fi
const char* password   = "0229043397";    // Reemplaza con tu contraseña
const char* ntpServer  = "pool.ntp.org";
const long  gmtOffset_sec = -10800;          // UTC-3 para Argentina
const int   daylightOffset_sec = 0;          // Sin horario de verano
int lastMinute = -1;                         // Control para no redibujar el reloj en cada loop

// --- COLORES EXCLUSIVOS DEL SCADA (Conversión de CSS Hex a RGB565) ---
#define COLOR_BG        tft.color565(238, 242, 246) // #eef2f6 Fondo general
#define COLOR_TOPBAR    tft.color565(221, 228, 234) // #dde4ea Gris barras
#define COLOR_BORDER    tft.color565(199, 209, 218) // #c7d1da Bordes
#define COLOR_TEXT_DARK tft.color565(26, 37, 48)    // #1a2530 Texto principal
#define COLOR_BLUE      tft.color565(37, 99, 235)   // #2563eb Tensión
#define COLOR_AMBER     tft.color565(217, 119, 6)   // #d97706 Corriente
#define COLOR_GREEN     tft.color565(22, 163, 74)   // #16a34a Consumo / OK
#define COLOR_RED       tft.color565(220, 38, 38)   // #dc2626 Alertas / Peligro
#define COLOR_WHITE     TFT_WHITE

// --- MÁQUINA DE ESTADOS PARA NAVEGACIÓN ---
enum Screen { SCREEN_HOME, SCREEN_VOLT, SCREEN_CURR, SCREEN_KW, SCREEN_MONTHLY };
Screen currentScreen = SCREEN_HOME;
bool refreshNeeded = true;

// --- VARIABLES GLOBALES Y SIMULACIÓN DE HISTORIALES ---
float V = 218.4, I = 4.4, kW = 0.96;
float kwHist[72]; // Historial del gráfico de líneas (Canvas)
int kwHistIdx = 0;
float weeklyKwh[7] = {3.2, 4.1, 3.8, 4.6, 5.1, 6.4, 2.9};
float monthlyKwh[12] = {142, 138, 151, 129, 167, 173, 0, 0, 0, 0, 0, 0};
const char* DAYS[7] = {"LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"};
const char* MONTHS_SHORT[12] = {"ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"};

// Estructura para emular el array de alertas de tu HTML
struct Alerta {
    char ts[15];
    char val[10];
    char lbl[15];
    bool isHigh; // true = high (rojo), false = low (naranja)
};
Alerta vAlerts[2] = {{"16:36", "208.3 V", "BAJA TENSION", false}, {"14:12", "236.1 V", "ALTA TENSION", true}};
Alerta iAlerts[1] = {{"15:48", "7.9 A", "SOBRECARGA", true}};

// Control de Tiempos
unsigned long ultimoTiempoSensores = 0;
unsigned long ultimoToqueTiempo = 0;
bool yaRegistroElToque = false;

// Factores de escala sensores
const float FACTOR_VOLTAJE = 0.025;   
const float FACTOR_CORRIENTE = 0.050; 

// --- DECLARACIÓN DE FUNCIONES GRÁFICAS ---
void goTo(Screen newScreen) {
    currentScreen = newScreen;
    refreshNeeded = true;
}

void updateClock() {
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
        return; // Si no se ha sincronizado la hora aún, no dibuja nada
    }

    // Solo redibuja si cambió el minuto o si forzamos el refresco completo (cambio de pantalla)
    if (timeinfo.tm_min != lastMinute || refreshNeeded) {
        char dateTimeStr[20];
        // %d/%m/%y genera dia/mes/año en 2 dígitos (ej: 05/07/26) y %H:%M la hora
        strftime(dateTimeStr, sizeof(dateTimeStr), "%d/%m/%y %H:%M", &timeinfo); 

        // Limpiar el espacio de la esquina superior derecha (ahora más ancho para la fecha + hora)
        tft.fillRect(190, 0, 130, 20, COLOR_TOPBAR);
        
        tft.setTextColor(COLOR_TEXT_DARK);
        tft.setTextFont(2);
        tft.setCursor(195, 2);
        tft.print(dateTimeStr);

        lastMinute = timeinfo.tm_min;
    }
}

void drawTopBar(const char* titulo) {
    tft.fillRect(0, 0, 320, 20, COLOR_TOPBAR);
    tft.drawFastHLine(0, 20, 320, COLOR_BORDER);
    tft.setTextColor(COLOR_TEXT_DARK);
    tft.setTextFont(2);
    tft.setCursor(8, 2);
    tft.print(titulo);
    
    // Forzamos el redibujado del reloj al cambiar de pantalla
    int tempMinute = lastMinute; 
    lastMinute = -1; 
    updateClock();
    lastMinute = tempMinute; // Restauramos para que el loop siga su curso normal
}

void drawBackButton() {
    tft.fillRoundRect(6, 23, 46, 24, 4, COLOR_WHITE);
    tft.drawRoundRect(6, 23, 46, 24, 4, COLOR_BORDER);
    
    tft.setTextDatum(MC_DATUM); 
    tft.setTextColor(COLOR_TEXT_DARK);
    tft.drawString("<", 6 + (46 / 2), 23 + (24 / 2), 2); 
    tft.setTextDatum(TL_DATUM); 
}

void renderHomeScreen() {
    if (refreshNeeded) {
        tft.fillScreen(COLOR_BG);
        drawTopBar("SCADA - MONOFASICO");
        tft.drawFastVLine(106, 20, 220, COLOR_BORDER);
        tft.drawFastVLine(213, 20, 220, COLOR_BORDER);
        
        tft.setTextColor(tft.color565(100, 110, 120));
        tft.setTextFont(1);
        tft.drawString("TENSION", 15, 30, 2);
        tft.drawString("CORRIENTE", 121, 30, 2);
        tft.drawString("CONSUMO", 228, 30, 2);
        
        tft.setTextColor(COLOR_BORDER);
        tft.drawString(">", 95, 220, 2);
        tft.drawString(">", 200, 220, 2);
        tft.drawString(">", 305, 220, 2);
        refreshNeeded = false;
    }

    bool vW = (V < 209 || V > 231);
    bool iW = (I > 7.5);

    tft.setTextFont(4);
    tft.fillRect(5, 70, 95, 40, COLOR_BG); 
    tft.setTextColor(vW ? COLOR_RED : COLOR_BLUE);
    tft.setCursor(10, 75); tft.print(V, 1); tft.setTextFont(2); tft.print(" V");

    tft.setTextFont(4);
    tft.fillRect(112, 70, 95, 40, COLOR_BG);
    tft.setTextColor(iW ? COLOR_RED : COLOR_AMBER);
    tft.setCursor(117, 75); tft.print(I, 2); tft.setTextFont(2); tft.print(" A");

    tft.setTextFont(4);
    tft.fillRect(218, 70, 95, 40, COLOR_BG);
    tft.setTextColor(COLOR_GREEN);
    tft.setCursor(223, 75); tft.print(kW, 2); tft.setTextFont(2); tft.print(" kW");

    tft.setTextFont(2);
    if (vW) tft.setTextColor(COLOR_RED); else tft.setTextColor(COLOR_BG);
    tft.drawString("!", 45, 180, 4);
    
    if (iW) tft.setTextColor(COLOR_RED); else tft.setTextColor(COLOR_BG);
    tft.drawString("!", 150, 180, 4);
}

void renderDetailScreen(const char* titulo, float valor, const char* unidad, uint16_t colorValor, bool warning, Alerta* alertas, int cantAlertas) {
    if (refreshNeeded) {
        tft.fillScreen(COLOR_BG);
        drawTopBar(titulo);
        drawBackButton();
        
        tft.fillRoundRect(220, 23, 90, 18, 4, warning ? tft.color565(254, 226, 226) : tft.color565(220, 252, 231));
        tft.drawRoundRect(220, 23, 90, 18, 4, warning ? COLOR_RED : COLOR_GREEN);
        tft.setTextColor(warning ? COLOR_RED : COLOR_GREEN);
        tft.setTextFont(1);
        tft.drawString(warning ? "ALERTA" : "NOMINAL", 235, 26, 2);

        tft.drawFastVLine(120, 45, 195, COLOR_BORDER);
        tft.setTextColor(tft.color565(120, 130, 140));
        tft.drawString("VALOR ACTUAL", 15, 55, 1);
        tft.drawString("HISTORIAL DE ALERTAS", 135, 55, 1);

        int yItem = 75;
        for (int i = 0; i < cantAlertas; i++) {
            tft.fillRoundRect(130, yItem, 180, 24, 3, COLOR_WHITE);
            tft.drawRoundRect(130, yItem, 180, 24, 3, COLOR_BORDER);
            tft.fillRect(130, yItem, 3, 24, alertas[i].isHigh ? COLOR_RED : COLOR_AMBER);
            
            tft.setTextColor(COLOR_TEXT_DARK);
            tft.drawString(alertas[i].ts, 138, yItem + 5, 1);
            tft.drawString(alertas[i].val, 175, yItem + 5, 2);
            tft.setTextColor(alertas[i].isHigh ? COLOR_RED : COLOR_AMBER);
            tft.drawString("!", 245, yItem + 4, 2);
            tft.drawString(alertas[i].lbl, 258, yItem + 6, 1);
            yItem += 28;
        }
        refreshNeeded = false;
    }

    tft.fillRect(5, 80, 110, 50, COLOR_BG);
    tft.setTextColor(colorValor);
    tft.setTextFont(4);
    tft.setCursor(10, 90);
    tft.print(valor, (unidad[0] == 'V') ? 1 : 2);
    tft.setTextFont(2);
    tft.print(unidad);
}

void renderKwScreen() {
    if (refreshNeeded) {
        tft.fillScreen(COLOR_BG);
        drawTopBar("CONSUMO ELECTRICO");
        drawBackButton();

        int startX = 40;
        for (int i = 0; i < 7; i++) {
            int barHeight = map(weeklyKwh[i], 0, 7, 0, 35);
            tft.fillRect(startX + (i * 38), 75 - barHeight, 18, barHeight, COLOR_GREEN);
            tft.drawRect(startX + (i * 38), 75 - barHeight, 18, barHeight, COLOR_BORDER);
            tft.setTextColor(COLOR_TEXT_DARK);
            tft.setTextFont(1);
            tft.drawString(DAYS[i], startX + (i * 38), 80, 1);
        }

        tft.drawRect(35, 105, 275, 65, COLOR_BORDER);
        tft.fillRect(36, 106, 273, 63, COLOR_WHITE);
        for(int g=1; g<4; g++) {
            tft.drawFastHLine(35, 105 + (g * 16), 275, tft.color565(240,242,245));
        }

        int kwBoxes[4] = {10, 87, 164, 241};
        const char* labels[4] = {"AHORA", "PROM", "PICO", "HOY"};
        
        for(int b=0; b<4; b++) {
            tft.fillRoundRect(kwBoxes[b], 180, 70, 32, 3, COLOR_WHITE);
            tft.drawRoundRect(kwBoxes[b], 180, 70, 32, 3, COLOR_BORDER);
            tft.setTextColor(tft.color565(130,140,150));
            tft.drawString(labels[b], kwBoxes[b] + 5, 183, 1);
        }

        tft.fillRoundRect(10, 217, 300, 19, 4, COLOR_WHITE);
        tft.drawRoundRect(10, 217, 300, 19, 4, COLOR_BORDER);
        tft.setTextColor(COLOR_GREEN);
        tft.drawString("CONSUMO MENSUAL", 102, 220, 2);

        refreshNeeded = false;
    }

    tft.fillRect(36, 106, 273, 63, COLOR_WHITE); 
    for (int i = 1; i < 72; i++) {
        int indexPrev = (kwHistIdx + i - 1) % 72;
        int indexCurr = (kwHistIdx + i) % 72;
        
        int x1 = 36 + ((i - 1) * 273) / 71;
        int x2 = 36 + (i * 273) / 71;
        int y1 = 168 - map(kwHist[indexPrev] * 100, 0, 250, 0, 58);
        int y2 = 168 - map(kwHist[indexCurr] * 100, 0, 250, 0, 58);
        
        tft.drawLine(x1, y1, x2, y2, COLOR_GREEN);
    }

    tft.setTextColor(COLOR_GREEN); tft.drawString(String(kW, 2), 15, 195, 2);
    tft.setTextColor(COLOR_GREEN); tft.drawString("0.91", 92, 195, 2);
    tft.setTextColor(COLOR_AMBER); tft.drawString("1.35", 169, 195, 2);
    tft.setTextColor(tft.color565(124, 58, 237)); tft.drawString("4.8", 246, 195, 2);
}

void renderMonthlyScreen() {
    if (refreshNeeded) {
        tft.fillScreen(COLOR_BG);
        drawTopBar("CONSUMO MENSUAL - kWh");
        drawBackButton();

        int cellW = 70;
        int cellH = 34;
        int colX[4] = {12, 88, 164, 240};
        int filaY[3] = {50, 92, 134};

        int item = 0;
        for (int f = 0; f < 3; f++) {
            for (int c = 0; c < 4; c++) {
                bool isCurrent = (item == 5); 
                bool hasData = (monthlyKwh[item] > 0);

                tft.fillRoundRect(colX[c], filaY[f], cellW, cellH, 4, isCurrent ? tft.color565(239, 246, 255) : COLOR_WHITE);
                tft.drawRoundRect(colX[c], filaY[f], cellW, cellH, 4, isCurrent ? COLOR_BLUE : COLOR_BORDER);
                
                tft.setTextColor(isCurrent ? COLOR_BLUE : COLOR_TEXT_DARK);
                tft.drawString(MONTHS_SHORT[item], colX[c] + 6, filaY[f] + 3, 1);

                if (hasData || isCurrent) {
                    tft.setTextColor(COLOR_GREEN);
                    tft.setTextFont(2);
                    tft.setCursor(colX[c] + 6, filaY[f] + 14);
                    if(hasData) tft.print((int)monthlyKwh[item]); else tft.print("--");
                } else {
                    tft.setTextColor(COLOR_BORDER);
                    tft.drawString("--", colX[c] + 6, filaY[f] + 14, 2);
                }
                item++;
            }
        }
        refreshNeeded = false;
    }
}

// --- PROCESAMIENTO ANALÓGICO DEL TOUCH ---
void comprobarTouch() {
    pinMode(XP, OUTPUT); digitalWrite(XP, HIGH);
    pinMode(XM, OUTPUT); digitalWrite(XM, LOW);
    pinMode(YP, INPUT);  pinMode(YM, INPUT);
    delay(5);
    int rawX = (analogRead(YM) + analogRead(YM)) / 2;

    pinMode(YP, OUTPUT); digitalWrite(YP, HIGH);
    pinMode(YM, OUTPUT); digitalWrite(YM, LOW);
    pinMode(XP, INPUT);  pinMode(XM, INPUT);
    delay(5);
    int rawY = (analogRead(XP) + analogRead(XP)) / 2;

    pinMode(XM, OUTPUT); pinMode(YP, OUTPUT);
    pinMode(XP, OUTPUT); pinMode(YM, OUTPUT);
    digitalWrite(YP, HIGH);

    bool reposo = (rawX >= 4000 || rawY < 400);
    
    if (!reposo) {
        if (!yaRegistroElToque && (millis() - ultimoToqueTiempo > 300)) {
            int px = map(rawY, 3600, 460, 0, 320);
            int x_comp = rawX - (int)(0.42 * rawY);
            int py = map(x_comp, 3150, 1820, 0, 240);

            Serial.print("Touch RAW -> X: "); Serial.print(rawX);
            Serial.print(" | Y: "); Serial.print(rawY);
            Serial.print("  ==> Calculado -> PX: "); Serial.print(px);
            Serial.print(" | PY: "); Serial.println(py);

            // Ruteador táctil
            if (currentScreen == SCREEN_HOME) {
                if (py > 20) {
                    if (px < 106) goTo(SCREEN_VOLT);
                    else if (px < 213) goTo(SCREEN_CURR);
                    else goTo(SCREEN_KW);
                }
            } 
            else { 
                if (px >= 0 && px <= 95 && py >= 0 && py <= 90) {
                    if (currentScreen == SCREEN_MONTHLY) goTo(SCREEN_KW);
                    else goTo(SCREEN_HOME);
                }
                else if (currentScreen == SCREEN_KW && py > 90) {
                    goTo(SCREEN_MONTHLY);
                }
            }
            yaRegistroElToque = true;
            ultimoToqueTiempo = millis();
        }
    } else {
        yaRegistroElToque = false;
    }
}

void setup() {
    Serial.begin(115200);
    
    // --- INICIO WI-FI ---
    Serial.print("Conectando a Wi-Fi");
    WiFi.begin(ssid, password);
    
    // Timeout de 10 segundos para no colgar el SCADA si el Wi-Fi falla
    int timeout = 0;
    while (WiFi.status() != WL_CONNECTED && timeout < 20) {
        delay(500);
        Serial.print(".");
        timeout++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println(" ¡Conectado!");
        
        // --- CONFIGURACIÓN NTP ---
        configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
        
        // Esperamos un instante a que el chip tome la hora real de la red
        struct tm timeinfo;
        int retry = 0;
        while(!getLocalTime(&timeinfo) && retry < 10) {
            delay(500);
            retry++;
        }
        Serial.println("Hora y fecha sincronizadas exitosamente.");
        
        // --- APAGAMOS EL WI-FI PARA LIBERAR EL ADC2 (Y QUE ANDE EL TOUCH) ---
        WiFi.disconnect(true);
        WiFi.mode(WIFI_OFF);
        Serial.println("Wi-Fi apagado. Pines ADC2 liberados para el Touch.");
    } else {
        Serial.println("\nNo se pudo conectar al Wi-Fi. Iniciando sin hora.");
    }

    analogSetWidth(12);

    for(int i=0; i<72; i++) kwHist[i] = 0.9;

    tft.init();
    tft.setRotation(1); 
    tft.fillScreen(COLOR_BG);
    goTo(SCREEN_HOME);
}

void loop() {
    updateClock(); // Mantiene el reloj y la fecha actualizados usando el RTC interno sin bloquear

    if (millis() - ultimoTiempoSensores > 500) {
        ultimoTiempoSensores = millis();
        int maxV = 0, minV = 4095;
        int maxI = 0, minI = 4095;
        unsigned long ventana = millis();
        
        while (millis() - ventana < 40) { 
            int sampleV = analogRead(PIN_ZMPT);
            int sampleI = analogRead(PIN_ACS);
            if (sampleV > maxV) maxV = sampleV; if (sampleV < minV) minV = sampleV;
            if (sampleI > maxI) maxI = sampleI; if (sampleI < minI) minI = sampleI;
        }
        
        V = ((maxV - minV) / 2.0) * 0.707 * FACTOR_VOLTAJE;
        I = ((maxI - minI) / 2.0) * 0.707 * FACTOR_CORRIENTE;
        kW = (V * I) / 1000.0;

        kwHist[kwHistIdx] = kW;
        kwHistIdx = (kwHistIdx + 1) % 72;
    }

    switch (currentScreen) {
        case SCREEN_HOME:    renderHomeScreen(); break;
        case SCREEN_VOLT:    renderDetailScreen("TENSION AC", V, " V", COLOR_BLUE, (V < 209 || V > 231), vAlerts, 2); break;
        case SCREEN_CURR:    renderDetailScreen("CORRIENTE AC", I, " A", COLOR_AMBER, (I > 7.5), iAlerts, 1); break;
        case SCREEN_KW:      renderKwScreen(); break;
        case SCREEN_MONTHLY: renderMonthlyScreen(); break;
    }

    comprobarTouch();
    delay(10);
}
