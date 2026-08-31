#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN   10
#define RST_PIN  9
#define BYTESXLECTURA 16
#define BUFFER_SIZE 18
#define BAUD_RATE 115200
#define PAGE_SIZE 4

const byte PAGINA_INICIO = 6;
const byte PAGINA_FIN    = 40;

MFRC522 mfrc522(SS_PIN, RST_PIN);
MFRC522::StatusCode status;
byte buffer[BUFFER_SIZE];
byte size = sizeof(buffer);

void setup() {
  Serial.begin(BAUD_RATE);
  SPI.begin();
  mfrc522.PCD_Init();
}

void loop() {
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial())
    return;

  bool fin = false;

  for (byte pagina = PAGINA_INICIO; pagina <= PAGINA_FIN && !fin; pagina += PAGE_SIZE) {
    status = (MFRC522::StatusCode)mfrc522.MIFARE_Read(pagina, buffer, &size);
    if (status != MFRC522::STATUS_OK) break;

    for (byte i = 0; i < BYTESXLECTURA && !fin; i++) {
      if (i == 0 && pagina == PAGINA_INICIO) i = 1;
      Serial.write(buffer[i]);

      if (buffer[i] == '}') fin = true; 
    }
  }

  Serial.println();
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}