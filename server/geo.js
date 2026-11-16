'use strict';
// Tabela de países (centro aproximado) usada para localizar manchetes no mapa.
// Formato: ISO|Nome|lat|lng|apelidos separados por vírgula (nomes em inglês, pois os feeds são em inglês).
const RAW = `
US|United States|39.8|-98.6|U.S.,US,USA,American,Washington,Pentagon,White House
CA|Canada|56.1|-106.3|Canadian,Ottawa
MX|Mexico|23.6|-102.5|Mexican
GT|Guatemala|15.8|-90.2|Guatemalan
HN|Honduras|15.2|-86.2|Honduran
SV|El Salvador|13.8|-88.9|Salvadoran
NI|Nicaragua|12.9|-85.2|Nicaraguan
CR|Costa Rica|9.7|-83.8|
PA|Panama|8.5|-80.8|Panamanian
CU|Cuba|21.5|-77.8|Cuban,Havana
HT|Haiti|19.0|-72.3|Haitian,Port-au-Prince
DO|Dominican Republic|18.7|-70.2|
JM|Jamaica|18.1|-77.3|Jamaican
CO|Colombia|4.6|-74.3|Colombian,Bogota
VE|Venezuela|6.4|-66.6|Venezuelan,Caracas
EC|Ecuador|-1.8|-78.2|Ecuadorian,Quito
PE|Peru|-9.2|-75.0|Peruvian,Lima
BO|Bolivia|-16.3|-63.6|Bolivian
BR|Brazil|-14.2|-51.9|Brazilian,Brasilia,Rio de Janeiro,Sao Paulo
PY|Paraguay|-23.4|-58.4|Paraguayan
UY|Uruguay|-32.5|-55.8|Uruguayan
AR|Argentina|-38.4|-63.6|Argentine,Argentinian,Buenos Aires
CL|Chile|-35.7|-71.5|Chilean,Santiago
GB|United Kingdom|54.0|-2.0|UK,U.K.,Britain,British,England,Scotland,Wales,London
IE|Ireland|53.4|-8.2|Irish,Dublin
FR|France|46.2|2.2|French,Paris,Macron
ES|Spain|40.5|-3.7|Spanish,Madrid
PT|Portugal|39.4|-8.2|Portuguese,Lisbon
DE|Germany|51.2|10.5|German,Berlin
NL|Netherlands|52.1|5.3|Dutch,Amsterdam
BE|Belgium|50.5|4.5|Belgian,Brussels
CH|Switzerland|46.8|8.2|Swiss,Geneva
AT|Austria|47.5|14.6|Austrian,Vienna
IT|Italy|41.9|12.6|Italian,Rome
GR|Greece|39.1|21.8|Greek,Athens
PL|Poland|51.9|19.1|Polish,Warsaw
CZ|Czech Republic|49.8|15.5|Czechia,Czech,Prague
SK|Slovakia|48.7|19.7|Slovak
HU|Hungary|47.2|19.5|Hungarian,Budapest
RO|Romania|45.9|25.0|Romanian,Bucharest
BG|Bulgaria|42.7|25.5|Bulgarian
RS|Serbia|44.0|21.0|Serbian,Belgrade
XK|Kosovo|42.6|20.9|Kosovan
BA|Bosnia|43.9|17.7|Bosnian
HR|Croatia|45.1|15.2|Croatian
AL|Albania|41.2|20.2|Albanian
MD|Moldova|47.4|28.4|Moldovan
UA|Ukraine|48.4|31.2|Ukrainian,Kyiv,Kiev,Kharkiv,Odesa,Crimea,Zelensky,Zelenskyy
BY|Belarus|53.7|27.9|Belarusian,Minsk
RU|Russia|61.5|90.0|Russian,Moscow,Kremlin,Putin
LT|Lithuania|55.2|23.9|Lithuanian
LV|Latvia|56.9|24.6|Latvian
EE|Estonia|58.6|25.0|Estonian
FI|Finland|61.9|25.7|Finnish,Helsinki
SE|Sweden|60.1|18.6|Swedish,Stockholm
NO|Norway|60.5|8.5|Norwegian,Oslo
DK|Denmark|56.3|9.5|Danish,Copenhagen
IS|Iceland|64.9|-19.0|Icelandic
GL|Greenland|71.7|-42.6|
TR|Turkey|39.0|35.2|Turkish,Türkiye,Ankara,Istanbul,Erdogan
GE|Georgia|42.3|43.4|Tbilisi
AM|Armenia|40.1|45.0|Armenian
AZ|Azerbaijan|40.1|47.6|Azerbaijani,Baku
SY|Syria|34.8|39.0|Syrian,Damascus,Aleppo
LB|Lebanon|33.9|35.9|Lebanese,Beirut,Hezbollah
IL|Israel|31.0|34.9|Israeli,Tel Aviv,Jerusalem,Netanyahu
PS|Palestine|31.4|34.4|Palestinian,Gaza,West Bank,Hamas,Rafah
JO|Jordan|30.6|36.2|Jordanian,Amman
IQ|Iraq|33.2|43.7|Iraqi,Baghdad
IR|Iran|32.4|53.7|Iranian,Tehran
SA|Saudi Arabia|23.9|45.1|Saudi,Riyadh
YE|Yemen|15.6|48.5|Yemeni,Houthi,Houthis,Sanaa
OM|Oman|21.5|55.9|Omani
AE|United Arab Emirates|23.4|53.8|UAE,Emirati,Dubai,Abu Dhabi
QA|Qatar|25.4|51.2|Qatari,Doha
KW|Kuwait|29.3|47.5|Kuwaiti
BH|Bahrain|26.0|50.6|Bahraini
EG|Egypt|26.8|30.8|Egyptian,Cairo
LY|Libya|26.3|17.2|Libyan,Tripoli
TN|Tunisia|33.9|9.5|Tunisian
DZ|Algeria|28.0|1.7|Algerian
MA|Morocco|31.8|-7.1|Moroccan
SD|Sudan|12.9|30.2|Sudanese,Khartoum,Darfur
SS|South Sudan|6.9|31.3|
ET|Ethiopia|9.1|40.5|Ethiopian,Addis Ababa,Tigray
ER|Eritrea|15.2|39.8|Eritrean
SO|Somalia|5.2|46.2|Somali,Mogadishu
KE|Kenya|-0.02|37.9|Kenyan,Nairobi
UG|Uganda|1.4|32.3|Ugandan,Kampala
TZ|Tanzania|-6.4|34.9|Tanzanian
RW|Rwanda|-1.9|29.9|Rwandan,Kigali
BI|Burundi|-3.4|29.9|Burundian
CD|DR Congo|-4.0|21.8|DRC,Democratic Republic of Congo,Democratic Republic of the Congo,Congolese,Kinshasa,Goma
CG|Republic of Congo|-0.2|15.8|Brazzaville
CF|Central African Republic|6.6|20.9|
TD|Chad|15.5|18.7|Chadian
NE|Niger|17.6|8.1|Nigerien,Niamey
NG|Nigeria|9.1|8.7|Nigerian,Abuja,Lagos
CM|Cameroon|7.4|12.4|Cameroonian
GH|Ghana|7.9|-1.0|Ghanaian
CI|Ivory Coast|7.5|-5.5|Côte d'Ivoire,Ivorian
ML|Mali|17.6|-4.0|Malian,Bamako
BF|Burkina Faso|12.2|-1.6|Burkinabe
SN|Senegal|14.5|-14.5|Senegalese,Dakar
GN|Guinea|9.9|-9.7|Guinean
SL|Sierra Leone|8.5|-11.8|
LR|Liberia|6.4|-9.4|Liberian
AO|Angola|-11.2|17.9|Angolan
ZM|Zambia|-13.1|27.8|Zambian
ZW|Zimbabwe|-19.0|29.2|Zimbabwean,Harare
MZ|Mozambique|-18.7|35.5|Mozambican
MW|Malawi|-13.3|34.3|Malawian
MG|Madagascar|-18.8|47.0|Malagasy
ZA|South Africa|-30.6|22.9|South African,Johannesburg,Pretoria,Cape Town
NA|Namibia|-22.9|18.5|Namibian
BW|Botswana|-22.3|24.7|
AF|Afghanistan|33.9|67.7|Afghan,Kabul,Taliban
PK|Pakistan|30.4|69.3|Pakistani,Islamabad,Karachi
IN|India|21.0|78.9|Indian,New Delhi,Delhi,Mumbai,Kashmir,Modi
BD|Bangladesh|23.7|90.4|Bangladeshi,Dhaka
LK|Sri Lanka|7.9|80.8|Sri Lankan,Colombo
NP|Nepal|28.4|84.1|Nepali,Nepalese,Kathmandu
MM|Myanmar|21.9|95.9|Burma,Burmese
TH|Thailand|15.9|100.9|Thai,Bangkok
KH|Cambodia|12.6|105.0|Cambodian
LA|Laos|19.9|102.5|Laotian
VN|Vietnam|14.1|108.3|Vietnamese,Hanoi
MY|Malaysia|4.2|102.0|Malaysian,Kuala Lumpur
SG|Singapore|1.35|103.8|Singaporean
ID|Indonesia|-0.8|113.9|Indonesian,Jakarta
PH|Philippines|12.9|121.8|Philippine,Filipino,Manila
CN|China|35.9|104.2|Chinese,Beijing,Shanghai,Xi Jinping
HK|Hong Kong|22.3|114.2|
TW|Taiwan|23.7|121.0|Taiwanese,Taipei
KP|North Korea|40.3|127.5|North Korean,Pyongyang,Kim Jong Un
KR|South Korea|35.9|127.8|South Korean,Seoul
JP|Japan|36.2|138.3|Japanese,Tokyo
MN|Mongolia|46.9|103.8|Mongolian
KZ|Kazakhstan|48.0|66.9|Kazakh
UZ|Uzbekistan|41.4|64.6|Uzbek
KG|Kyrgyzstan|41.2|74.8|Kyrgyz
TJ|Tajikistan|38.9|71.3|Tajik
TM|Turkmenistan|39.0|59.6|Turkmen
AU|Australia|-25.3|133.8|Australian,Sydney,Canberra,Melbourne
NZ|New Zealand|-41.0|174.9|
PG|Papua New Guinea|-6.3|143.9|
FJ|Fiji|-17.7|178.1|Fijian
`;

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const COUNTRIES = RAW.trim().split('\n').map((line) => {
  const [iso, name, lat, lng, alias] = line.split('|');
  const names = [name].concat((alias || '').split(',').filter(Boolean));
  // nomes mais longos primeiro, para "South Sudan" ganhar de "Sudan"
  names.sort((a, b) => b.length - a.length);
  const re = new RegExp('(?<![A-Za-z])(' + names.map(esc).join('|') + ')(?![A-Za-z])');
  return { iso, name, lat: +lat, lng: +lng, re };
});

/** Retorna o país citado mais cedo no texto (ou null). */
function locate(text) {
  let best = null;
  let bestAt = Infinity;
  let bestLen = 0;
  for (const c of COUNTRIES) {
    const m = c.re.exec(text);
    if (!m) continue;
    if (m.index < bestAt || (m.index === bestAt && m[0].length > bestLen)) {
      best = c; bestAt = m.index; bestLen = m[0].length;
    }
  }
  return best;
}

/** Bandeira em emoji a partir do código ISO. */
function flag(iso) {
  if (!iso || iso.length !== 2 || iso === 'XK') return '🏳️';
  return String.fromCodePoint(...[...iso.toUpperCase()].map((ch) => 0x1f1e6 + ch.charCodeAt(0) - 65));
}

/** Deslocamento determinístico para marcadores do mesmo país não ficarem empilhados. */
function jitter(seed, spread = 1.6) {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) { h ^= seed.charCodeAt(i); h = Math.imul(h, 16777619); }
  const a = ((h >>> 0) % 1000) / 1000;
  const b = ((h >>> 10) % 1000) / 1000;
  return [(a - 0.5) * 2 * spread, (b - 0.5) * 2 * spread];
}

module.exports = { COUNTRIES, locate, flag, jitter };
