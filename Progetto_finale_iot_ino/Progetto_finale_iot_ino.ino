/**
 *    IOT laboratorio HW-3
 *        The Arduino sketch must be modified accordingly to perform the following tasks:
          i. register itself on the on Catalog (refer to Exercise 1 Lab Software – part 2).
          ii. send information about temperature, presence and noise via MQTT
          iii. receive actuation commands via MQTT
          iv. receive messages to be displayed on the LCD monitor via MQTT

 */

/**
 * questo è un codice sperando che sia il definitivo, modifiche apportate :
 *    -un solo setpoint della temperatura, in accordo con il bot di telegram e la 
 *      dashboard, dato questo setpoint ci sarà un range di attivazione degli attuatori
 *      di +/- 10 gradi senza presenza, +/- 5 con presenza
 *    -aumento lo sleeptime di fine ciclo all'interno del ciclo while per dare più
 *     possibilit all'ascolto dei messaggi mqtt. ho notato che legge un messaggio ogni 
 *     mqtt.monitor(), ma ciò sembra decisamente lento, soprattutto per il primo ciclo
 *     in cui deve ricevere in risposta i basenames per i vari sensori
 *    -set registered ha problemi, in particolare con la string& subtopic. cercare un modo
 *     per inviare un messaggio chiaro senza appesantire troppo
 *        l'idea è quella di mandare indietro un senml in cui all'interno del valore
 *        della risorsa cè appunto la risorsa che è stata letta mentre nel basename 
 *        cè il valore del nuovo id da assegnare
 *        
 */

#include <MQTTclient.h>
#include <Bridge.h>
#include <BridgeServer.h>
#include <BridgeClient.h>
#include <math.h>
#include <LiquidCrystal_PCF8574.h>


float setPointTemp = 20.0;

float tempFanMin = 0;
float tempFanMax = 0;
float tempLedMin = 0;
float tempLedMax = 0;

float temp;

const int lightPin = 12;
const int ledPin = 11;
const int tempPin = A1;
const long int R0 = 100000;
const int beta = 4275;
const int sleepTime = 20;

const int fanPin = 10;
/* Valore corrente speed da 0 a 255 */
float currentSpeed = 0;
float ledPower = 0;
int lightValue = 0;
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

/**
 * parte per comunicazione mqtt
 */

String myBaseTopicLed = "/tiot/26/catalog/led";   //ledVerde
String myBaseTopicTmp = "/tiot/26/catalog/tmp";
String myBaseTopicFan = "/tiot/26/catalog/fan";   
String myBaseTopicHeat = "/tiot/26/catalog/heat";   
String myBaseTopicPresence = "/tiot/26/catalog/prs";

/**
 * questi sotto sono i topic di registrazione al catalog 
 */
String myBaseTopicLedReg = "/tiot/26/catalog/led/res";   //ledVerde
String myBaseTopicTmpReg = "/tiot/26/catalog/tmp/res";
String myBaseTopicFanReg = "/tiot/26/catalog/fan/res";   
String myBaseTopicHeatReg = "/tiot/26/catalog/heat/res";   
String myBaseTopicPresenceReg = "/tiot/26/catalog/prs/res";
String myBaseTopicResponse = "/tiot/26/catalog/+/res";
String myBaseTopicChangeTemperature = "/tiot/26/catalog/tmp/change";      /*TOPIC CHIAMATO DAL BOT TRAMITE IL CATALOG PER CAMBIARE TEMPERATURA*/
String myBaseTopicLedOnOff = "/tiot/26/catalog/led/onoff";


String basenameTmp = "unregistered";
String basenameLed = "unregistered";
String basenameFan = "unregistered";
String basenamePresence = "unregistered"; 
String basenameHeat = "unregistered";


void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Bridge.begin();
  pinMode(tempPin, INPUT);
  pinMode(fanPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  analogWrite(fanPin, currentSpeed);
  pinMode(lightPin, OUTPUT);
  digitalWrite(lightPin, lightValue);

  pinMode(soundPin, INPUT);

  pinMode(pirPin, INPUT);
  attachInterrupt(digitalPinToInterrupt(soundPin), checkSound, FALLING);

  setupSoundEvents(soundEvents);
   
  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.home();
  lcd.clear();
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  digitalWrite(13, HIGH);
  mqtt.begin("mqtt.eclipse.org", 1883);
  mqtt.subscribe(myBaseTopicResponse, setRegistered);
  mqtt.subscribe(myBaseTopicChangeTemperature, setTmpValue);
  mqtt.subscribe(myBaseTopicLedOnOff, setLedValue);
  /*
  mqtt.subscribe(myBaseTopicLedReg, setRegistered);
  mqtt.subscribe(myBaseTopicTmpReg, setRegistered);
  mqtt.subscribe(myBaseTopicFanReg, setRegistered);
  mqtt.subscribe(myBaseTopicHeatReg, setRegistered);
  mqtt.subscribe(myBaseTopicPresenceReg, setRegistered);
  */
  Serial.println("Almeno qui ci arrivo!");
  
  Serial.println("Lab 3.3 Starting:");
}

void loop() {
  // put your main code here, to run repeatedly:
  mqtt.monitor();
  /**
   * monitor attiva la comunicazione in arrivo dai topic
   * a cui si è iscritti, serve a chiamare la callback
   */
  /**
   * Settaggio parametri di temperatura
  */
  if (flag==0){   
    tempFanMin = setPointTemp;
    tempFanMax = setPointTemp + 10.0;
    tempLedMin = setPointTemp - 10.0;
    tempLedMax = setPointTemp;
  }
  else if (flag==1){    
    tempFanMin = setPointTemp;
    tempFanMax = setPointTemp + 5.0;
    tempLedMin = setPointTemp - 5.0;
    tempLedMax = setPointTemp;
  }
  
   temp = checkTemp();
   Serial.println(String(temp));

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
   * COMUNICAZIONE MQTT 
   */
  Serial.println("sto prima della creazione json");
  String json = senMlEncode("tmp", temp, "C", basenameTmp);
  mqtt.publish(myBaseTopicTmp, json);
  Serial.print("published tmp on topic");
  Serial.println(json);
  Serial.println(myBaseTopicTmp);

  json = senMlEncode("Heat", ledPower, "", basenameHeat);
  mqtt.publish(myBaseTopicHeat, json);
  json = senMlEncode("fan", currentSpeed, "", basenameFan);
  mqtt.publish(myBaseTopicFan, json);
  json = senMlEncode("light", (float)lightValue, "", basenameLed);
  mqtt.publish(myBaseTopicLed, json);
  json = senMlEncode("pres", float(flag), "", basenamePresence);  
  mqtt.publish(myBaseTopicPresence, json);
 
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
//    if (Serial.available()){
//      listenSerial();
//    }
    mqtt.monitor();
  }
}

void setLedValue(const String& topic, const String& subtopic, const String& message){
/*  deserializeJson(doc_rec, message);
      if(int(doc_rec["v"])==0 || int(doc_rec["v"])==1){
        digitalWrite(ledPin, (int)doc_rec["v"]);  
  }*/
  char tmp[100] = "", value[10] = "", resource[10] = "";
  message.toCharArray(tmp, 99);
  splitSet(tmp,value, resource);
  lightValue = atoi(value);
  if(strcmp(resource, "led")&&(lightValue==0 || lightValue == 1)){
   digitalWrite(lightPin, lightValue);
   
  }  
}
void setTmpValue(const String& topic, const String& subtopic, const String& message){
/*  deserializeJson(doc_rec, message);
      if(int(doc_rec["v"])==0 || int(doc_rec["v"])==1){
        digitalWrite(ledPin, (int)doc_rec["v"]);  
  }*/
  char tmp[100] = "", value[10] = "", resource[10] = "";
  message.toCharArray(tmp, 99);
  splitSet(tmp,value, resource);
  
  if(strcmp(resource, "tmp")){
   setPointTemp = atof(value);
  }  
}

void splitSet(char tmp[100], char value[10], char resource[10]){
  /*io so che il basename lo trovo dopo bn e resource dopo il campo n*/
  int i=0, j=0;
  
  while(i<99){
    if(tmp[i++] == "\""){
        if (tmp[i++]== "n"){
          if (tmp[i++]== "\"") {
            while(tmp[i++]!="\"");    /*salto gli spazi e = e mi posiziono sul bn da leggere*/
              while(tmp[i]!="\""){
              resource[j]= tmp[i];
              i++;
              j++;
              }
              resource[j]="\0";
          }
        }
    }
    if(tmp[i++] == "\""){
      if (tmp[i++]== "v"){
        if (tmp[i++]== "\"") {
          while(tmp[i++]!="\"");    /*salto gli spazi e = e mi posiziono sul bn da leggere*/
            while(tmp[i]!="\""){
            value[j]= tmp[i];
            i++;
            j++;
            }
            value[j]="\0";
        }
      }
    }
  }
  
}

void setRegistered(const String& topic, const String& subtopic, const String& message){
  /**
   * il parametro subtopic non funziona correttamente, si mangia la penultima lettera 
   * e ritorna solo l'ultima, non gli ultimi caratteri che vanno a formare il subtopic
   *  tmp, fan, led, pres
   *  
  String basenameTmp = "unregistered";
  String basenameLed = "unregistered";
  String basenameFan = "unregistered";
  String basenamePresence = "unregistered"; 

   
  DeserializationError err = deserializeJson(doc_rec, message);
  
  String iNeedName = doc_rec["bn"];
  Serial.println(iNeedName);
  
  if (doc_rec["e"][0]["n"] == "tmp"){ 
    basenameTmp = iNeedName;
  }
  else if (doc_rec["e"][0]["n"] == "fan"){
    basenameFan = iNeedName;
  }
  else if (doc_rec["e"][0]["n"] == "led"){
    basenameLed = iNeedName;
  }
  else if (doc_rec["e"][0]["n"] == "pres"){
    basenamePresence = iNeedName;
  }
  else if (doc_rec["e"][0]["n"] == "heat"){
    basenameHeat = iNeedName;
  }
  */
  /*ORA PROVO A FARLO IN MANUALE*/
  /*per prima cosa devo estrarre il bn*/
  char tmp[100] = "", newName[10] = "", resource[10] = "";
  message.toCharArray(tmp, 99);
  split(tmp, newName, resource);
  
  if (strcmp(resource, "tmp")){ 
    basenameTmp = (String)newName;
  }
  else if (strcmp(resource, "fan")){
    basenameFan = (String)newName;
  }
  else if (strcmp(resource, "led")){
    basenameLed = (String)newName;
  }
  else if (strcmp(resource, "pres")){
    basenamePresence = (String)newName;
  }
  else if (strcmp(resource, "heat")){
    basenameHeat = (String)newName;
  }
  
}

void split(char tmp[100], char newName[10], char resource[10]){
  /*io so che il basename lo trovo dopo bn e resource dopo il campo n*/
  int i=0, j=0;
  
  while(i<99){
    if(tmp[i++] == "\""){
      if (tmp[i++]== "b"){
        if (tmp[i++]== "n"){
          if (tmp[i++]== "\"") {
            while(tmp[i++]!="\"");    /*salto gli spazi e = e mi posiziono sul bn da leggere*/
              while(tmp[i]!="\""){
              newName[j]= tmp[i];
              i++;
              j++;
              }
              newName[j]="\0";
          }
        }
      }
    }
    if(tmp[i++] == "\""){
      if (tmp[i++]== "n"){
        if (tmp[i++]== "\"") {
          while(tmp[i++]!="\"");    /*salto gli spazi e = e mi posiziono sul bn da leggere*/
            while(tmp[i]!="\""){
            resource[j]= tmp[i];
            i++;
            j++;
            }
            resource[j]="\0";
        }
      }
    }
  }
  
}

/**
 * funzione rileva temperatura
 */
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
  return TC;
}

/**
 * crea il json
 */
String senMlEncode(String res, float v, String unit, String bn){
  /**
   * params:  res = risorsa in uso. in questo caso sarà 
   *                sempre la temperatura
   *          v = valore della risorsa. la prendo dalla 
   *              checktemp tramite la variabile temp
   *              (si potrebbe semplificare per un caso reale
   *              ma preferisco mantenere leggibilità)
   *          unit = unità di misura del valore della risorsa
   *          {"bn" = basename,
   *           "c" = 0, 
   *           "e" = {"n" = res,
   *                  "v" = value,
   *                  "u" = unit}
   *          }
   *                  
   */
  Serial.println(res);
  /*
  doc_snd.clear();
  doc_snd["bn"] = bn;
  doc_snd["c"] =  "0";
  doc_snd["e"][0]["n"] = res;
  doc_snd["e"][0]["v"] = v;
  doc_snd["e"][0]["u"] = unit;
  */
  /*provo manualmente*/
  char bnChar[15], resChar[10], unitChar[2], vChar[10]; 
  bn.toCharArray(bnChar, 15);
  res.toCharArray(resChar, 10);
  unit.toCharArray(unitChar, 2);
  dtostrf(v, 4, 2, vChar);
  
  char output[150] = "";
  strcat(output, "{\"bn\" : \""); 
  strcat(output, bnChar);
  strcat(output, "\",\"c\" : \"0\",");
  strcat(output, "\"e\" : {\"n\" : \"") ;
  strcat(output, resChar);
  strcat(output, "\",\"v\" : \"");
  strcat(output, vChar) ;
  strcat(output, "\",\"u\" : \""); 
  strcat(output, unitChar);
  strcat(output, "\"}}\0");
  
  char ciao[] = "ciaone";
  strcpy(ciao, output);
  String myString = String(ciao);
  /*
  String myString=String(output);
  */
  Serial.println(myString);
  
  Serial.println(output);
  return myString;
}

void setupSoundEvents(int vect[]) {
  int i;
  for (i = 0; i < TIME_INTERVAL; i++) {
    vect[i] = 0;
  }
}

void checkPresence(){
  if (digitalRead(pirPin)==HIGH){
    if (digitalRead(soundPin)==LOW){
      flag = 1;
      checkTimePir = millis();
      Serial.println("Movimento rilevato!");
    }
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
  }
}
