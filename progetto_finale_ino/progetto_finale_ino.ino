/**
 *    IOT laboratorio HW-2
 *    esercizio 1
 *    todo: SMART Home Controller
 *          parte 1, ventola che si accende proporzionalmente
 *          con temperatura 25-30
 */

#include <math.h>
#include <LiquidCrystal_PCF8574.h>

/**
 * Set di temperature, 4 valori per presenza di persone 
 * e 4 per l'assenza
 */
float tempFanMinNoPeople = 25;
float tempFanMaxNoPeople = 30;
float tempLedMinNoPeople = 20;
float tempLedMaxNoPeople = 25;
float tempFanMinWithPeople = 25;
float tempFanMaxWithPeople = 35;
float tempLedMinWithPeople = 15;
float tempLedMaxWithPeople = 25;

int tempFanMin = 0;
int tempFanMax = 0;
int tempLedMin = 0;
int tempLedMax = 0;

float temp;

const int ledPin = 11;
const int tempPin = A1;
const long int R0 = 100000;
const int beta = 4275;
const int sleepTime = 5;

const int fanPin = 10;
/* Valore corrente speed da 0 a 255 */
float currentSpeed = 0;
float ledPower = 0;

const int soundPin = 7;
const unsigned long timeoutPir = 1800000;         /* timeout pir, circa 30 minuto 1800 secondi */
volatile unsigned long checkTimePir = 0;
unsigned long currentMillis;

/**
 * QUESTO FLAG INDICA LA PRESENZA DI PERSONE, 0 ASSENZA E 1 PRESENZA (sensor fusion, slide 03, pag +-70)
 */
int flag = 0;

const int pirPin = 4;
const unsigned long soundInterval = 600000;      /* 10 minuti in millis */
const unsigned long timeoutSound = 2400000;      /* 40 minuti timeout */
volatile unsigned long checkTimeSound = 0;
int countSoundEvent = 0;

int setupLCD = 0;
LiquidCrystal_PCF8574 lcd(0x27);


/* Variabili per Finestra Mobile */
const int TIME_INTERVAL = 10 + 1, EVENTS_NUM = 50;
int soundEvents[TIME_INTERVAL];

/* Variabili per LCD */
int timeout = 60000;


void setup() {
  /* Primo setup dei componenti */
  pinMode(tempPin, INPUT);
  pinMode(fanPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  analogWrite(fanPin, currentSpeed);

  pinMode(soundPin, INPUT);

  pinMode(pirPin, INPUT);
  attachInterrupt(digitalPinToInterrupt(soundPin), checkSound, FALLING);

  setupSoundEvents(soundEvents);

  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.home();
  lcd.clear();
  
  Serial.begin(9600);
  Serial.print("Lab 2 Starting");
  Serial.setTimeout(timeout); /* Timeout riferito alla lettura dell'input settato a 1 minuto per permettere all'utente di scrivere */
}

void loop() {
  /**
   * Settaggio parametri di temperatura
  */
  if (flag==0){   
    tempFanMin = tempFanMinNoPeople;
    tempFanMax = tempFanMaxNoPeople;
    tempLedMin = tempLedMinNoPeople;
    tempLedMax = tempLedMaxNoPeople;
  }
  else if (flag==1){    
    tempFanMin = tempFanMinWithPeople;
    tempFanMax = tempFanMaxWithPeople;
    tempLedMin = tempLedMinWithPeople;
    tempLedMax = tempLedMaxWithPeople;
  }

  temp = checkTemp();
  /**
   * Controllo ventilatore
   */
  if (temp < tempFanMax && temp > tempFanMin){
    currentSpeed = (temp-tempFanMin)/(tempFanMax-tempFanMin)*255.0;
    analogWrite(fanPin, currentSpeed);
    Serial.print("Temperatura :");
    Serial.print(temp);
    Serial.print(" velocita :");
    Serial.println(currentSpeed);
  }
  else{
    currentSpeed = 0;
    analogWrite(fanPin, currentSpeed);
  }
  /**
   * Controllo led
   */
  if (temp < tempLedMax && temp > tempLedMin){
    ledPower = abs(temp-tempLedMax)/abs(tempLedMin-tempLedMax)*255.0;
    analogWrite(ledPin, ledPower);
  }
  else {
    ledPower = 0;
    analogWrite(ledPin, ledPower);
  }

  /**
   *  Questo current millis indica il tempo trasorso dall'ultimo movimento
   *  rilevato dal sensore PIR, ovvero dall'ultima volta che ho registrato 
   *  il checkTimePir, se questo valore scade significa che non c'è nessuno.
   */
  
  currentMillis = millis();
  if (currentMillis - checkTimePir >= timeoutPir) {
    flag = 0;
  }

  /**
   * Al posto della delay uitilizzo un ciclo while 
   * in cui attento il passare del tempo e checko la presenza di movimenti
   * il ciclo while dura 5 secondi, prima di ogni ciclo vado a cambiare la pagina
   * del LCD
   */
  lookLCD();
 
  int delayMillis = int(millis()/1000);
  while (int(millis()/1000) - delayMillis <= sleepTime){
    checkPresence(); 
    if (Serial.available()){
      listenSerial();
    }
  }
}

float checkTemp(){
  int vDigit = analogRead(tempPin);
  /**
   * Calcolo il valore di R, successivamente
   * uso il datasheet per ricavare le formule di conversione e 
   * calcolo T, per poi convertire in Celsius
  */
  float R = ((1023.0/vDigit)-1.0);
  R = R0*R;
  float loga = log(R/R0)/beta;
  float TK = 1.0/((loga)+(1.0/298.15));
  float TC = TK-273.15;
  Serial.print("TEMPERATURA RICEVUTA = ");
  Serial.println(String(TC));
  return TC;
}


/**
 * Forse sarebbe meglio mettere come interrupt il sensore di
 * rumore, avendo a disposizione questi sensori si portrebbe 
 * diminuire la sensibilità del sensore di prossimità così che
 * ogni ciclo del loop principale possa catturare comunque le 
 * variazioni del sensore, mentre quello di rumore (più semplice
 * e basilare, e soprattutto solo digitale) si potrebbe impostare
 * sull'interrupt
 */
 
void setupSoundEvents(int vect[]) {
  int i;
  for (i = 0; i < TIME_INTERVAL; i++) {
    vect[i] = 0;
  }
}

void checkPresence(){
  if (digitalRead(pirPin)==HIGH){
    flag = 1;
    checkTimePir = millis();
    Serial.println("Movimento rilevato!");
  }
}

void checkSound(){
  /* Implementazione Buffer Circolare */
  int index, count=0, i, tail;
  
  index = int(millis()/60000)%(TIME_INTERVAL);
  /* Metto a zero il successivo minuto */
  tail = (index + 1)%TIME_INTERVAL;
  soundEvents[tail] = 0;
  /* Aggiorno gli eventi della finestra corrente */
  if (digitalRead(soundPin)==LOW){
    soundEvents[index]++;
    delay(200);
    Serial.println("Suono ricevuto!");
    Serial.print("SOUND EVENTS NEL BLOCCO = ");
    Serial.println(String(soundEvents[index]));
  }
  /* Controllo se nella finestra ci sono abbastanza eventi */
  for(i = 0; i < TIME_INTERVAL; i++) {
    count += soundEvents[i];
  }
  if (count >= EVENTS_NUM) {
    flag = 1;
  } 
  else {
    flag = 0;
  };
}

void lookLCD(){
  /*
   * In base al setup corrente faccio la print della schermata 
   */
  if (setupLCD == 0){
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("T=");
    lcd.print(String(temp));
    lcd.print(" Pres:");
    lcd.print(String(flag));
    lcd.setCursor(0, 1);
    lcd.print("AC:");
    lcd.print(String(currentSpeed/2.55));
    lcd.print(" HT:");
    lcd.print(String(ledPower/2.55));
    setupLCD = 1;

    Serial.print("T=");
    Serial.print(String(temp));
    Serial.print(" Pres:");
    Serial.print(String(flag));
    Serial.println("");
    Serial.print("AC:");
    Serial.print(String(currentSpeed/2.55));
    Serial.print(" HT:");
    Serial.print(String(ledPower/2.55));
  }
  else if(setupLCD == 1){
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("AC m:");
    lcd.print(String(tempFanMin));
    lcd.print(" M:");
    lcd.print(String(tempFanMax));
    lcd.setCursor(0, 1);
    lcd.print("HT m:");
    lcd.print(String(tempLedMin));
    lcd.print(" M:");
    lcd.print(String(tempLedMax));
    setupLCD = 0;


    Serial.print("AC m:");
    Serial.print(String(tempFanMin));
    Serial.print(" M:");
    Serial.print(String(tempFanMax));
    Serial.println("");
    Serial.print("HT m:");
    Serial.print(String(tempLedMin));
    Serial.print(" M:");
    Serial.print(String(tempLedMax));
  }
}

/**
 * Dalla read devo leggere 8 valori, in sequenza saranno
  int tempFanMinNoPeople = 25;
  int tempFanMaxNoPeople = 30;
  int tempLedMinNoPeople = 20;
  int tempLedMaxNoPeople = 25;
  int tempFanMinWithPeople = 25;
  int tempFanMaxWithPeople = 35;
  int tempLedMinWithPeople = 15;
  int tempLedMaxWithPeople = 25;

  I VALORI IN INPUT DEVONO ESSERE DIVISI DA /
 */
void listenSerial(){
  char data[8][4] = {};
  char inByte[41] = {};

  //esempio stringa 25.1/26.0/20.0/21.0/23.0/28.0/15.0/22.0

  if (Serial.available() > 0) {
    int i, k = 0, j;

    
    int availableBytes = Serial.available();
    for(int i=0; i<availableBytes; i++){
       inByte[i] = char(Serial.read());
    }
    
    for (i=0 ; i<40 ; i=i+5){
      for(j=0 ; j<4; j++){
        data[k][j] = inByte[j+i];
      }
      k++;
    }
    tempFanMinNoPeople = atof(data[0]);
    tempFanMaxNoPeople = atof(data[1]);
    tempLedMinNoPeople = atof(data[2]);
    tempLedMaxNoPeople = atof(data[3]);
    tempFanMinWithPeople = atof(data[4]);
    tempFanMaxWithPeople = atof(data[5]);
    tempLedMinWithPeople = atof(data[6]);
    tempLedMaxWithPeople = atof(data[7]);
    Serial.println("SETUP DELLE TEMPERATURE AVVENUTO CON SUCCESSO");
  }
} 
