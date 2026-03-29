// MODE: 'demo' | 'local' | 'aws'
// Set VITE_MODE=local in website/.env to use local server
// Set VITE_MODE=aws  in website/.env to use deployed AWS API Gateway
export const MODE = import.meta.env.VITE_MODE || 'demo'

export const API_ENDPOINT =
  MODE === 'local' ? (import.meta.env.VITE_LOCAL_SERVER || 'http://localhost:3001') :
  MODE === 'aws'  ? (import.meta.env.VITE_API_ENDPOINT || '') :
  '' // demo mode — no API call

export const CONNECT_PHONE = import.meta.env.VITE_CONNECT_PHONE || '(804) 555-3112';
export const SPEAK_RESPONSES = true;

// ── English demo responses (grounded in uploaded Richmond docs) ───────────────
export const DEMO_RESPONSES = {

  'snap|food stamp|ebt|benefit|nutrition|food assistance|work requirement':
    'Important: SNAP work requirements changed in November 2025. If you are 64 or under, you must meet work requirements unless exempt. The dependent child exemption now only applies if your child is under 14. Exemptions for homelessness, veterans status, and foster care (ages 18–24) were removed on November 1, 2025. To check your benefits or report changes, visit CommonHelp.virginia.gov or contact your local Department of Social Services.',

  'food|hungry|meal|pantry|foodbank|feed':
    'The Central Virginia Foodbank serves all Richmond residents at (804) 521-2500. For SNAP food assistance, visit CommonHelp.virginia.gov to apply or check your benefits. Note that SNAP work requirements changed in November 2025 — contact your local Department of Social Services with questions.',

  'freeze|cold|winter|heat|pipe|warming shelter|hypothermia|frostbite':
    'Stay safe in freezing temperatures: Never heat your home with a cooking stove or run a car in a closed garage — carbon monoxide is deadly. If power goes out, insulate one room with blankets and share body heat. Leave a trickle of water running to prevent pipes from bursting. Wear layers and a hat outside — 40% of body heat is lost from the head. Hypothermia sets in below 95°F body temperature. Check local news for temporary warming shelters in Richmond during outages.',

  'ice|immigration|deport|undocumented|detained|arrest|officer|customs|cbp':
    'All people in the U.S. have rights regardless of immigration status. Key points: Stay calm — do not run, argue, or resist. You have the right to remain silent. Do NOT open your door — officers need a warrant signed by a judge to enter. ICE forms are NOT judge-signed warrants. If stopped, ask: "Are you from ICE or CBP?" For 24/7 emergency support call: 1-855-HELP-MY-FAMILY (1-855-435-7693). For Richmond legal help: Central Virginia Legal Aid Society (804) 648-1012.',

  'mental health|depression|anxiety|stress|refugee|immigrant|trauma|counseling':
    'Mental health support is available for immigrants and refugees in Richmond. The Richmond Behavioral Health Authority crisis line is available 24/7 at (804) 819-4100. CrossOver Healthcare Ministry provides culturally sensitive care at (804) 655-4800. National Crisis Line: 988. You do not need insurance or documentation to access crisis services. Would you like help finding a specific type of support?',

  'prepare|emergency|disaster|safety plan|family plan|storm|power outage':
    'Build a family emergency plan: Identify emergency contacts and memorize their numbers. Designate someone to pick up your children from school. Keep phones charged, flashlights, a radio, and enough water for several days. During winter storms, set up a warm "shelter in place" room — insulate windows with blankets and stay together. Do not drive during ice storms. Check local news for Richmond emergency shelter announcements.',

  'legal|court|lawyer|eviction|rights|warrant|attorney':
    'Central Virginia Legal Aid Society provides FREE legal help to low-income Richmond residents: (804) 648-1012. For immigration legal issues, visit immigrantjustice.org/for-immigrants. Richmond Law School Clinic: (804) 289-8189. Remember: you have the right to remain silent with any law enforcement, and officers need a judge-signed warrant to enter your home.',

  'health|doctor|medical|insurance|medicaid|clinic':
    'CrossOver Healthcare Ministry offers free primary care at (804) 655-4800. The Richmond & Henrico Health District has sliding-scale services at (804) 205-3500. Medicaid enrollment assistance: (804) 646-7201. You do not need documentation to access emergency medical care.',

  'rent|housing|evict|landlord|homeless':
    'Richmond rental assistance: RRHA at (804) 780-4200. Department of Social Services Emergency Assistance at 900 E Marshall St, (804) 646-7201. If you receive an eviction notice, contact Central Virginia Legal Aid immediately at (804) 648-1012 — you have legal rights in the eviction process.',

  'utility|electric|water|gas|bill|power':
    'LIHEAP helps with utility bills — call (804) 646-7201. Dominion Energy and Richmond Gas Works both have hardship payment plans. During winter outages, check local news for Richmond warming shelters.',

  'job|work|employment|career|resume':
    'Richmond Works Employment Services: (804) 646-5600. Virginia Employment Commission: 700 E Main St. For immigrants and refugees, CrossOver and local non-profits also offer job placement support.',

  'default': "I'm here to help Richmond residents — including immigrants and refugees — access city services and community resources 24/7. I can assist with SNAP benefits, freezing weather safety, immigration rights, mental health, housing, healthcare, and more. What do you need help with today?"
};

// ── RVA311 Service Categories ──────────────────────────────────────────────
export const RVA311_CATEGORIES = [
  {
    id: 'emergency',
    name: 'Emergency Preparedness',
    nameEs: 'Preparación para Emergencias',
    icon: '⚠️',
    description: 'To report City issues from severe storms: downed trees blocking roads, non-functioning traffic signals. Call non-Emergency Police 804-646-5100.'
  },
  {
    id: 'roads',
    name: 'Roads, Alleys, Sidewalks and Ramps',
    nameEs: 'Carreteras, Callejones, Aceras y Rampas',
    icon: '🏗️',
    description: 'Report potholes, damaged sidewalks, alley maintenance, and ADA ramp issues.'
  },
  {
    id: 'lights',
    name: 'Lights, Signs and Signals',
    nameEs: 'Luces, Señales y Semáforos',
    icon: '🚦',
    description: 'Report streetlight outages, damaged signs, malfunctioning traffic signals.'
  },
  {
    id: 'trees',
    name: 'Trees and Vegetation',
    nameEs: 'Árboles y Vegetación',
    icon: '🌿',
    description: 'Request tree planting, trimming, or removal. Report fallen trees or overgrown vegetation on city property.'
  },
  {
    id: 'parks',
    name: 'Parks and Public Spaces',
    nameEs: 'Parques y Espacios Públicos',
    icon: '🏞️',
    description: 'Report park maintenance issues, playground damage, public space concerns.'
  },
  {
    id: 'collection',
    name: 'Collection and Cleaning',
    nameEs: 'Recolección y Limpieza',
    icon: '🧹',
    description: 'Request trash cans, report missed collections, leaf vacuum service, street cleaning.'
  },
  {
    id: 'stormwater',
    name: 'Stormwater and Drainage',
    nameEs: 'Aguas Pluviales y Drenaje',
    icon: '🌧️',
    description: 'Report flooding, clogged storm drains, drainage issues.'
  },
  {
    id: 'sewer',
    name: 'Sewer and Wastewater',
    nameEs: 'Alcantarillado y Aguas Residuales',
    icon: '🔧',
    description: 'Report sewer backups, wastewater issues, manhole problems.'
  },
  {
    id: 'taxes',
    name: 'Taxes, Billing and Licensing Inquiries',
    nameEs: 'Impuestos, Facturación y Licencias',
    icon: '💰',
    description: 'Questions about property taxes, business licenses, billing inquiries.'
  },
  {
    id: 'zoning',
    name: 'Zoning and Code Enforcement',
    nameEs: 'Zonificación y Cumplimiento de Códigos',
    icon: '🏢',
    description: 'Report code violations, zoning inquiries, property maintenance complaints.'
  },
  {
    id: 'parking',
    name: 'Parking and Vehicles',
    nameEs: 'Estacionamiento y Vehículos',
    icon: '🚗',
    description: 'Report abandoned vehicles, parking violations, vehicle-related issues.'
  },
  {
    id: 'investigation',
    name: 'Request Investigation',
    nameEs: 'Solicitar Investigación',
    icon: '🔍',
    description: 'Request investigation into speeding, illegal dumping, graffiti, and other concerns.'
  },
  {
    id: 'animals',
    name: 'Animals, Vermin and Infestations',
    nameEs: 'Animales, Plagas e Infestaciones',
    icon: '🐾',
    description: 'Report stray animals, pest infestations, animal control needs.'
  },
  {
    id: 'business',
    name: 'Business Support Services',
    nameEs: 'Servicios de Apoyo Empresarial',
    icon: '💼',
    isNew: true,
    webOnly: true,
    externalUrl: '/biznavigator.html',
    description: 'Start or grow your business in Richmond. Access step-by-step guides for business registration, permits, licensing, zoning, and local resources. Available online only.'
  },
  {
    id: 'support',
    name: 'Request Support Services',
    nameEs: 'Solicitar Servicios de Apoyo',
    icon: '🤝',
    description: 'Request assistance with aging and disability services, social services, housing support, and community resources.',
    subcategories: [
      {
        id: 'seeking_worker',
        name: 'Seeking Worker Support',
        nameEs: 'Buscando Apoyo para Trabajadores',
        icon: '🤲',
        description: 'This request type is used to submit a request for worker support services. Access employment assistance, job training referrals, and workforce development programs available through the City of Richmond and partner organizations.'
      },
      {
        id: 'aging',
        name: 'Request Aging and Disability Care and Support',
        nameEs: 'Solicitar Cuidado y Apoyo para Envejecimiento y Discapacidad',
        icon: '🧡',
        highlight: true,
        description: 'This request type is used to submit a request or inquiry to the City for assistance applying for benefit programs through the Office of Aging and Disability.\n\nThe agency assists adults 55 and older and persons 18 or older with disabilities in exploring available programs, confirming eligibility requirements and submitting applications or requests for services from City departments and/or outside agencies. This includes programs related to:\n\n• Housing Insecurity or unsheltered persons\n• Food insecurity or meal delivery assistance\n• Transportation Assistance\n• Other benefit assistance based on specific needs\n\nOnce your request has been submitted, someone from the Office of Aging and Disabilities will contact you within two (2) business days to help identify available programs and resources. For additional information on the Office of Aging and Disability programs and services, visit our page on RVA.gov'
      },
      {
        id: 'family_crisis',
        name: 'Family Crisis Fund - Water Recovery',
        nameEs: 'Fondo de Crisis Familiar - Recuperación de Agua',
        icon: '💧',
        paused: true,
        description: 'This service is currently PAUSED. The Family Crisis Fund - Water Recovery program provides emergency assistance for water-related crises. Please check back later or contact 311 for alternative resources.'
      },
      {
        id: 'police_event',
        name: 'How to Request Police Attendance at Community Event',
        nameEs: 'Cómo Solicitar Presencia Policial en Evento Comunitario',
        icon: '👮',
        description: 'Request police presence or attendance at a community event. Submit details about your event including date, time, location, expected attendance, and any specific security needs.'
      },
      {
        id: 'immigrant_services',
        name: 'Immigrant and Refugee Services',
        nameEs: 'Servicios para Inmigrantes y Refugiados',
        icon: '🌍',
        highlight: true,
        isNew: true,
        description: 'Access multilingual support, legal aid referrals, and community resources for immigrants and refugees in Richmond. This service connects you with trusted community partners including:\n\n• IRC Richmond (International Rescue Committee)\n• ReEstablish Richmond\n• Sacred Heart Center\n• Afghan Association of Virginia\n• African Community Network\n• Central Virginia Legal Aid Society\n\nAvailable in English, Spanish, Arabic, Dari, and Pashto. No personal information or immigration status will be collected. For 24/7 emergency immigration support call: 1-855-HELP-MY-FAMILY (1-855-435-7693).'
      },
      {
        id: 'mental_health',
        name: 'Mental Health and Crisis Support',
        nameEs: 'Salud Mental y Apoyo en Crisis',
        icon: '💚',
        isNew: true,
        description: 'Access crisis intervention, counseling referrals, and behavioral health services for all Richmond residents including immigrants and refugees.\n\n• Richmond Behavioral Health Authority 24/7 Crisis Line: (804) 819-4100\n• National Crisis Line: 988\n• CrossOver Healthcare Ministry: (804) 655-4800\n\nYou do not need insurance or documentation to access crisis services. Culturally sensitive care is available.'
      },
      {
        id: 'food_assistance',
        name: 'Food and Nutrition Assistance',
        nameEs: 'Asistencia Alimentaria y Nutricional',
        icon: '🍎',
        isNew: true,
        description: 'Access food pantries, SNAP benefits information, meal delivery programs, and emergency food assistance.\n\n• Central Virginia Foodbank: (804) 521-2500\n• SNAP application: CommonHelp.virginia.gov\n• Department of Social Services: (804) 646-7201\n\nNote: SNAP work requirements changed in November 2025. Contact your local DSS office for the latest eligibility information.'
      },
      {
        id: 'housing',
        name: 'Housing and Rental Assistance',
        nameEs: 'Asistencia de Vivienda y Alquiler',
        icon: '🏠',
        isNew: true,
        description: 'Request help with rental assistance, emergency housing, RRHA programs, and housing insecurity.\n\n• Richmond Redevelopment and Housing Authority: (804) 780-4200\n• Department of Social Services Emergency Assistance: (804) 646-7201\n• Central Virginia Legal Aid (eviction help): (804) 648-1012\n\nIf you receive an eviction notice, you have legal rights — contact Legal Aid immediately.'
      }
    ]
  }
];

// ── Privacy Notice ─────────────────────────────────────────────────────────
export const PRIVACY_NOTICE_EN = `This is a private service request and will not be posted publicly. It is not mandatory but you can create an account or sign in with your existing account, both of which can be done by continuing with your request. If you do not sign in, you will only receive email notifications for changes in request status. There will be no PII collected.`;

export const PRIVACY_NOTICE_ES = `Esta es una solicitud de servicio privada y no será publicada públicamente. No es obligatorio pero puede crear una cuenta o iniciar sesión con su cuenta existente, ambas opciones se pueden hacer continuando con su solicitud. Si no inicia sesión, solo recibirá notificaciones por correo electrónico para cambios en el estado de la solicitud. No se recopilarán datos personales identificables.`;

// ── Spanish demo responses (grounded in uploaded Richmond docs) ───────────────
export const DEMO_RESPONSES_ES = {

  'snap|estampillas|ebt|beneficio|nutrición|asistencia de alimentos|requisito de trabajo':
    'Importante: Los requisitos de trabajo de SNAP cambiaron en noviembre de 2025. Si tiene 64 años o menos, debe cumplir los requisitos de trabajo a menos que esté exento. La exención por hijo dependiente ahora solo aplica si su hijo tiene menos de 14 años. Las exenciones por falta de vivienda, veteranos y cuidado de crianza (18–24 años) fueron eliminadas el 1 de noviembre de 2025. Para verificar sus beneficios: CommonHelp.virginia.gov o llame a su Departamento de Servicios Sociales local.',

  'comida|hambre|alimento|despensa|banco de alimentos|comer':
    'El Banco de Alimentos de Virginia Central atiende a todos los residentes de Richmond al (804) 521-2500. Para solicitar SNAP, visite CommonHelp.virginia.gov. Los requisitos de trabajo de SNAP cambiaron en noviembre de 2025 — contacte a su Departamento de Servicios Sociales con preguntas.',

  'frío|congelar|invierno|calefacción|tubería|refugio caliente|hipotermia|congelamiento':
    'Seguridad en temperaturas de congelación: Nunca caliente su hogar con la estufa de cocina ni encienda un auto en un garaje cerrado — el monóxido de carbono es mortal. Si se va la luz, aísle un cuarto con cobijas y compartan calor corporal. Deje correr un chorrito de agua para prevenir que las tuberías se revienten. Use ropa en capas y gorro — el 40% del calor corporal se pierde por la cabeza. Consulte las noticias locales para refugios de calefacción en Richmond.',

  'ice|inmigración|deportar|indocumentado|detenido|arresto|oficial|aduanas|cbp':
    'Todas las personas en EE.UU. tienen derechos sin importar su estatus migratorio. Puntos clave: Mantenga la calma — no corra, argumente ni resista. Tiene derecho a guardar silencio. NO abra su puerta — los oficiales necesitan una orden firmada por un juez para entrar. Los formularios de ICE NO son órdenes firmadas por jueces. Si lo detienen, pregunte: "¿Es usted de ICE o CBP?" Para apoyo de emergencia 24/7: 1-855-HELP-MY-FAMILY (1-855-435-7693). Ayuda legal en Richmond: (804) 648-1012.',

  'salud mental|depresión|ansiedad|estrés|refugiado|inmigrante|trauma|consejería':
    'Hay apoyo de salud mental disponible para inmigrantes y refugiados en Richmond. La línea de crisis de Richmond BHA está disponible 24/7 al (804) 819-4100. CrossOver Healthcare Ministry ofrece atención culturalmente sensible al (804) 655-4800. Línea Nacional de Crisis: 988. No necesita seguro ni documentos para acceder a servicios de crisis.',

  'preparar|emergencia|desastre|plan de seguridad|plan familiar|tormenta|apagón':
    'Plan de emergencia familiar: Identifique contactos de emergencia y memorice sus números. Designe a alguien para recoger a sus hijos de la escuela. Mantenga teléfonos cargados, linternas, radio y agua para varios días. En tormentas de invierno, preparen un cuarto cálido — aíslen las ventanas con cobijas y permanezcan juntos. No maneje durante tormentas de hielo.',

  'legal|corte|abogado|desalojo|derechos|orden|attorney':
    'La Sociedad de Ayuda Legal de Virginia Central ofrece ayuda legal GRATIS: (804) 648-1012. Para asuntos de inmigración: immigrantjustice.org/for-immigrants. Recuerde: tiene derecho a guardar silencio y los oficiales necesitan una orden firmada por un juez para entrar a su hogar.',

  'salud|médico|doctor|seguro|medicaid|clínica|medicina':
    'CrossOver Healthcare Ministry: atención primaria gratuita al (804) 655-4800. Distrito de Salud de Richmond y Henrico: servicios a escala móvil al (804) 205-3500. Inscripción a Medicaid: (804) 646-7201. No necesita documentos para recibir atención médica de emergencia.',

  'renta|vivienda|desalojo|arrendador|sin hogar|alquiler':
    'Asistencia de alquiler en Richmond: RRHA al (804) 780-4200. Servicios Sociales en 900 E Marshall St, (804) 646-7201. Si recibe un aviso de desalojo, contacte a Ayuda Legal inmediatamente al (804) 648-1012.',

  'electricidad|agua|gas|factura|servicio|utilidad|apagón':
    'LIHEAP ayuda con facturas de servicios — llame al (804) 646-7201. Dominion Energy y Richmond Gas Works tienen planes de pago por dificultades. Durante apagones de invierno, consulte las noticias para refugios de calefacción en Richmond.',

  'trabajo|empleo|carrera|curriculum|desempleo':
    'Richmond Works: servicios de empleo al (804) 646-5600. Comisión de Empleo de Virginia: 700 E Main St. Para inmigrantes y refugiados, CrossOver y organizaciones locales también ofrecen apoyo.',

  'default': 'Estoy aquí para ayudar a los residentes de Richmond — incluyendo inmigrantes y refugiados — a acceder a servicios y recursos comunitarios las 24 horas. Puedo ayudar con beneficios SNAP, seguridad en el frío, derechos migratorios, salud mental, vivienda, atención médica y más. ¿En qué le puedo ayudar hoy?'
};

// ── UI translations ───────────────────────────────────────────────────────────
export const TRANSLATIONS = {
  en: {
    title: 'Richmond City Resource Assistant',
    subtitle: '24/7 Community Support Line',
    available: 'Available 24 hours, 7 days a week',
    howItWorks: 'How It Works',
    step1: 'Ask your question', step1d: 'Speak into the mic or type your message',
    step2: 'Get instant help', step2d: 'AI searches Richmond City resources for you',
    step3: 'Community follow-up', step3d: 'Non-profit partners notified to help further',
    callTitle: '📞 Call the IVR Line',
    callNote: 'Powered by Amazon Connect',
    resourcesTitle: 'Available Resources',
    langNote: '🌐 English & Spanish support available',
    resources: ['Housing & Rental Assistance','Food & SNAP Benefits','Healthcare & Medicaid','Immigration & Legal Rights','Freezing Weather Safety','Mental Health Support','Job Training & Employment','Family Emergency Planning'],
    onlineLabel: 'Assistant Online',
    demoNote: 'Add your API Gateway URL to .env for live AWS responses.',
    placeholder: 'Type your question here...',
    listeningPlaceholder: 'Listening... speak now',
    send: 'Send', holdToSpeak: 'Hold to Speak', releaseToSend: 'Release to send',
    noSpeech: 'Speech input not supported in this browser. Use Chrome or Edge.',
    statusReady: '● Ready', statusListening: '🎙 Listening...', statusThinking: '⏳ Thinking...', statusSpeaking: '🔊 Speaking...',
    welcome: "Hello! I'm the Richmond City Resource Assistant, available 24/7. I can help with SNAP benefits, freezing weather safety, immigration rights, mental health, housing, healthcare, and more. How can I help you today?",
    errorMsg: "I'm having trouble connecting right now. Please try again or call 311 for immediate assistance.",
    switchedToEs: '¡Hola! Ahora estoy en español. Puedo ayudarle con beneficios SNAP, seguridad en el frío, derechos migratorios, salud mental y más. ¿En qué le puedo ayudar?',
    langBtn: 'ES',
  },
  es: {
    title: 'Asistente de Recursos de Richmond',
    subtitle: 'Línea de Apoyo Comunitario 24/7',
    available: 'Disponible 24 horas, 7 días a la semana',
    howItWorks: 'Cómo Funciona',
    step1: 'Haga su pregunta', step1d: 'Hable al micrófono o escriba su mensaje',
    step2: 'Obtenga ayuda inmediata', step2d: 'La IA busca recursos de Richmond para usted',
    step3: 'Seguimiento comunitario', step3d: 'Socios sin fines de lucro serán notificados',
    callTitle: '📞 Llame a la Línea IVR',
    callNote: 'Desarrollado por Amazon Connect',
    resourcesTitle: 'Recursos Disponibles',
    langNote: '🌐 Servicio disponible en inglés y español',
    resources: ['Asistencia de Vivienda y Alquiler','Alimentos y Beneficios SNAP','Salud y Medicaid','Inmigración y Derechos Legales','Seguridad en Temperaturas de Congelación','Apoyo de Salud Mental','Capacitación Laboral y Empleo','Planificación de Emergencias Familiares'],
    onlineLabel: 'Asistente en Línea',
    demoNote: 'Agregue su URL de API Gateway al .env para respuestas en vivo de AWS.',
    placeholder: 'Escriba su pregunta aquí...',
    listeningPlaceholder: 'Escuchando... hable ahora',
    send: 'Enviar', holdToSpeak: 'Mantenga para Hablar', releaseToSend: 'Suelte para enviar',
    noSpeech: 'El micrófono no es compatible con este navegador. Use Chrome o Edge.',
    statusReady: '● Listo', statusListening: '🎙 Escuchando...', statusThinking: '⏳ Procesando...', statusSpeaking: '🔊 Hablando...',
    welcome: '¡Hola! Soy el Asistente de Recursos de Richmond, disponible las 24 horas. Puedo ayudarle con beneficios SNAP, seguridad en el frío, derechos migratorios, salud mental, vivienda y más. ¿En qué le puedo ayudar hoy?',
    errorMsg: 'Tengo problemas para conectarme. Por favor intente de nuevo o llame al 311 para asistencia inmediata.',
    switchedToEn: "Hello! Switching back to English. How can I help you today?",
    langBtn: 'EN',
  }
};
