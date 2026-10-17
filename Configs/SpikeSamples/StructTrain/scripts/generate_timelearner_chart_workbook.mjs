import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const [payloadPath, outputDir] = process.argv.slice(2);
if (!payloadPath || !outputDir) {
  throw new Error("usage: generate_timelearner_chart_workbook.mjs <payload.json> <output-dir>");
}

const payload = JSON.parse(await fs.readFile(payloadPath, "utf8"));
await fs.mkdir(outputDir, { recursive: true });

function niceMajorUnit(span, targetTicks = 8) {
  const raw = Math.max(span / targetTicks, 0.001);
  const power = 10 ** Math.floor(Math.log10(raw));
  const normalized = raw / power;
  const factor = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return factor * power;
}

function styleLineChart(chart, title, yTitle, xMajorUnit, yFormat) {
  chart.title = title;
  chart.titleTextStyle.typeface = "Arial";
  chart.titleTextStyle.fontSize = 12;
  chart.hasLegend = false;
  chart.xAxis = {
    axisType: "textAxis",
    numberFormatCode: "0.0",
    numberFormatSourceLinked: false,
    tickLabelInterval: xMajorUnit,
    textStyle: { typeface: "Arial", fontSize: 10 },
    majorGridlines: null,
    minorGridlines: null,
  };
  chart.xAxis.title.text = "Время, мс";
  chart.yAxis = {
    numberFormatCode: yFormat,
    numberFormatSourceLinked: false,
    textStyle: { typeface: "Arial", fontSize: 10 },
    majorGridlines: { fill: "#D9E0E5", style: "solid", width: 0.5 },
    minorGridlines: null,
  };
  chart.yAxis.title.text = yTitle;
}

const workbook = Workbook.create();
const chartSummary = [];
const previewSheets = [];
for (const item of payload.trials ?? []) {
  const trialNum = Number(item.trial ?? 0);
  const sheetName = `T${String(trialNum + 1).padStart(2, "0")}`;
  const sheet = workbook.worksheets.add(sheetName);
  sheet.showGridLines = false;

  const inputTimes = (item.input_ms ?? []).map((time) => Number(Number(time).toFixed(9)));
  const outputTimes = (item.output_ms ?? []).map((time) => Number(Number(time).toFixed(9)));
  const eventStart = Number(item.start_ms ?? 0);
  const eventEnd = Math.max(Number(item.end_ms ?? 100), eventStart + 0.001);
  if (inputTimes.length) {
    sheet.getRange(`AA1:AB${inputTimes.length + 1}`).values = [
      ["input_time_ms", "input_level"],
      ...inputTimes.map((time) => [time, 1]),
    ];
  }
  if (outputTimes.length) {
    sheet.getRange(`AD1:AE${outputTimes.length + 1}`).values = [
      ["output_time_ms", "output_level"],
      ...outputTimes.map((time) => [time, 2]),
    ];
  }
  const eventChart = sheet.charts.add("scatter", {
    from: { row: 0, col: 0 },
    extent: { widthPx: 1080, heightPx: 370 },
  });
  eventChart.title = `Вход и выход нейрона — пример ${trialNum + 1}; выходных импульсов: ${outputTimes.length}`;
  eventChart.titleTextStyle.typeface = "Arial";
  eventChart.titleTextStyle.fontSize = 12;
  eventChart.legend = { position: "top", textStyle: { typeface: "Arial", fontSize: 10 } };
  eventChart.xAxis = {
    numberFormatCode: "0.0",
    numberFormatSourceLinked: false,
    majorUnit: niceMajorUnit(eventEnd - eventStart),
    textStyle: { typeface: "Arial", fontSize: 10 },
    majorGridlines: null,
    minorGridlines: null,
  };
  eventChart.xAxis.title.text = "Время от первого стимула, мс";
  eventChart.yAxis = { deleted: true };
  const inputSeries = eventChart.series.add("Входные импульсы");
  inputSeries.xValuesSource = `'${sheetName}'!$AA$2:$AA$${inputTimes.length + 1}`;
  inputSeries.valuesSource = `'${sheetName}'!$AB$2:$AB$${inputTimes.length + 1}`;
  if (outputTimes.length) {
    const outputSeries = eventChart.series.add("Импульсы нейрона");
    outputSeries.xValuesSource = `'${sheetName}'!$AD$2:$AD$${outputTimes.length + 1}`;
    outputSeries.valuesSource = `'${sheetName}'!$AE$2:$AE$${outputTimes.length + 1}`;
  }
  eventChart.setPosition("A1", "N13");

  const trace = item.trace ?? [];
  if (trace.length) {
    const timeValues = trace.map((sample) => Number(sample.time_ms));
    const traceStart = Math.min(...timeValues);
    const traceEnd = Math.max(...timeValues);
    const timeMajor = niceMajorUnit(Math.max(traceEnd - traceStart, 0.001));
    const traceData = [
      ["time_ms", "Soma min", "Soma max", "LTZone min", "LTZone max"],
      ...trace.map((sample) => [
        Number(Number(sample.time_ms).toFixed(1)),
        sample.soma_min == null ? null : Number(sample.soma_min),
        sample.soma_max == null ? null : Number(sample.soma_max),
        sample.ltz_min == null ? null : Number(sample.ltz_min),
        sample.ltz_max == null ? null : Number(sample.ltz_max),
      ]),
    ];
    const traceRange = `AA1:AE${traceData.length}`;
    sheet.getRange(traceRange).values = traceData;

    const somaChart = sheet.charts.add("line", sheet.getRange(`AA1:AC${traceData.length}`));
    styleLineChart(somaChart, "Потенциал на выходе сомы", "Потенциал, модельные единицы", timeMajor, "0.000");
    somaChart.series.items[0].line = { fill: "#137A52", style: "solid", width: 2 };
    somaChart.series.items[1].line = { fill: "#69A98A", style: "solid", width: 1.5 };
    somaChart.legend = { position: "top", textStyle: { typeface: "Arial", fontSize: 9 } };
    somaChart.setPosition("A15", "G31");

    const ltzData = [
      ["time_ms", "LTZone min", "LTZone max"],
      ...trace.map((sample) => [
        Number(Number(sample.time_ms).toFixed(1)),
        sample.ltz_min == null ? null : Number(sample.ltz_min),
        sample.ltz_max == null ? null : Number(sample.ltz_max),
      ]),
    ];
    sheet.getRange(`AF1:AH${ltzData.length}`).values = ltzData;
    const ltzChart = sheet.charts.add("line", sheet.getRange(`AF1:AH${ltzData.length}`));
    styleLineChart(ltzChart, "Потенциал LTZone", "Потенциал, модельные единицы", timeMajor, "0.000");
    ltzChart.series.items[0].line = { fill: "#6554A4", style: "solid", width: 2 };
    ltzChart.series.items[1].line = { fill: "#A195CB", style: "solid", width: 1.5 };
    ltzChart.legend = { position: "top", textStyle: { typeface: "Arial", fontSize: 9 } };
    ltzChart.setPosition("H15", "N31");
    chartSummary.push({ trial: trialNum, hasTrace: true, chartCount: 3, sampleCount: trace.length });
  } else {
    chartSummary.push({ trial: trialNum, hasTrace: false, chartCount: 1, sampleCount: 0 });
  }

  previewSheets.push({ sheetName, trial: trialNum, hasTrace: trace.length > 0 });
}

workbook.recalculate();
for (const item of previewSheets) {
  const preview = await workbook.render({
    sheetName: item.sheetName,
    range: item.hasTrace ? "A1:N31" : "A1:N13",
    scale: 1,
    format: "png",
  });
  await fs.writeFile(path.join(outputDir, `trial_${item.trial}.png`), new Uint8Array(await preview.arrayBuffer()));
}
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(path.join(outputDir, "timelearner_charts.xlsx"));
console.log(JSON.stringify({ sheets: chartSummary.length, charts: chartSummary }));
