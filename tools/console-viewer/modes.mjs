const leftRail = -82.5;
const groups={
  body:['herrajesFijos','herrajesY','herrajesX','herrajesOptica','base','deck','front','switchmount','toggle','arch','pod','camera','driveFix','movingY','movingX','mechanism','phone','rails','harness','belt','electronics'],
  move:['herrajesFijos','herrajesY','herrajesX','rails','movingY','movingX','driveFix','belt','phone','mechanism'],
  floor:['herrajesFijos','base','electronics','power','front','switchmount','toggle','harness'],
};
const modes={
  hardware:{title:'Dónde va cada tornillo',text:'Dorado para el M3 avellanado y azul para el M3 de botón. Tocá una familia para resaltarla en el conjunto.',
    groups:['herrajesFijos','herrajesY','herrajesX','herrajesOptica','base','deck','rails','movingY','movingX','arch'],
    tags:[
      ['#7213 · Avellanado','Une las mitades, los asientos de las guías, la tapa y el pórtico. La cabeza queda al ras del plástico.',[-62,88,46.8],'T_7213_'],
      ['#7219 · Botón','Fija los rieles, los patines, los motores, la MKS y la corredera. Las dos familias M3 usan Allen de 2 mm.',[leftRail,98,95],'T_7219_'],
      ['Tuerca cuadrada M3','Entra de costado en el plástico. Los patines y motores ya llevan su propia rosca.',[leftRail,58,87],'Q_M3_']]},

  outside:{title:'Consola compacta',text:'La cámara mira al centro de la cama. La ventana lateral permite introducir el teléfono y revisar las correas. La pantalla y el interruptor quedan al frente.',
    groups:groups.body,tags:[
      ['Interruptor general I / O','Palanca NKK S301T en el frente derecho.',[48,8,27],'S301T_'],
      ['Cámara a 100 mm del vidrio','La capota y la cámara suben 10 mm o bajan 5 mm desde la posición de referencia.',[-5,137,219],'Capota_'],
      ['iPhone centrado bajo el lente','La punta queda alineada con el centro de los bloques laterales.',[-5,101,55],'iPhone14']]},
  travel:{title:'Recorrido del carro',text:'Mové X e Y. En verde se ven los dos carriles laterales. El naranja muestra el espacio del patín transversal a la altura actual del puente.',
    groups:groups.move,tags:[
      ['Dos patines laterales','Se comprueba el cuerpo completo de ambos MGN9H hasta cada extremo de los rieles de 250 mm.',[leftRail,138,99],'Patin_Y_'],
      ['Carro transversal','El bloque de 39,9 mm se desplaza por el riel de 150 mm. La punta sigue su movimiento.',[-5,152,139],'Patin_X'],
      ['Motores posteriores','El cuerpo y la placa de los motores quedan detrás del recorrido de la punta al fondo.',[21,275,88],'NEMA17_']]},
  electronics:{title:'Debajo del teléfono',text:'El piso aloja las placas. La alimentación entra por atrás en corriente continua. Los cargadores de pared quedan fuera de la caja.',
    groups:groups.floor,tags:[
      ['Raspberry Pi 5','La cámara y la MKS se conectan por USB. Sobre la Pi queda el ventilador.',[39,114,37],'Raspberry_'],
      ['MKS DLC32 y los dos drivers','Dos tornillos delanteros y dos lengüetas traseras retienen el panel de servicio.',[-31,195,18],'MKS_'],
      ['Conversión de corriente','El rectángulo ámbar reserva 68 × 50 × 27 mm para la conversión interna. Falta seleccionar y validar el conjunto de alimentación.',[-42,92,28],'Reserva_']]},
  switch:{title:'Interruptor frontal',text:'Es el NKK S301T. La punta de la palanca sobresale de la tuerca y queda protegida dentro del borde. Podés simular sus dos posiciones.',
    groups:['detalleSwitch','switchmount','toggle'],tags:[
      ['Palanca de dos posiciones','Los 32° de recorrido quedan libres dentro del rebaje.',[48,8,25],'S301T_palanca'],
      ['Tuerca hexagonal','El casquillo atraviesa un panel de 3 mm, con un segundo orificio pequeño para impedir el giro.',[53,26,35],'S301T_tuerca'],
      ['Dos bornes con tornillo','Quedan accesibles desde dentro. La propuesta es un corte general en corriente continua.',[48,58,20],'S301T_terminal']]},
  optics:{title:'Altura de la cámara',text:'La distancia de referencia es 100 mm del vidrio al centro del lente. La corredera mantiene la cámara sobre el centro del teléfono.',
    groups:['herrajesOptica','arch','pod','camera','phone','rails','mechanism'],tags:[
      ['Centro del lente','En la posición nominal queda 65 mm por encima de la superficie de apoyo de los rieles.',[-5,138,155],'C922_lente'],
      ['Vidrio del teléfono','El vidrio está 35 mm por debajo de esa referencia.',[-5,85,55],'Area_activa_'],
      ['Soporte impreso regulable','Lente a 95–110 mm del vidrio. Los montantes quedan fuera de los carriles.',[21,152,186],'Portico_camara_']]}
};

export {modes};
