import { jsPDF } from 'jspdf';

function text(value, fallback = 'Not available') {
  return value === undefined || value === null || value === '' ? fallback : String(value);
}

function pdfText(value, fallback = 'Not available') {
  return text(value, fallback)
    .replace(/\r\n?/g, '\n')
    .replace(/```[^\n]*\n?/g, '')
    .replace(/```/g, '')
    .replace(/[—–−]/g, '-')
    .replace(/[“”]/g, '"')
    .replace(/[‘’]/g, "'")
    .replace(/…/g, '...')
    .replace(/\u00a0/g, ' ')
    .replace(/\t/g, '    ')
    .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, '')
    .replace(/[^\x09\x0a\x0d\x20-\x7e]/g, '');
}

function severityColor(value) {
  const severity = String(value || '')
    .trim()
    .toLowerCase();
  if (severity === 'critical') return [220, 55, 82];
  if (severity === 'high') return [220, 125, 35];
  if (severity === 'medium') return [210, 155, 35];
  if (severity === 'low') return [5, 150, 105];
  return [35, 45, 55];
}

export function createAnalysisPdf(analysis, bugReport, date = new Date()) {
  const pdf = new jsPDF({ unit: 'pt', format: 'a4' });
  const margin = 42;
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const contentWidth = pageWidth - margin * 2;
  const bottom = pageHeight - margin;
  const lineHeight = 12;
  let y = margin;

  pdf.setFont('helvetica', 'normal');

  const addPage = () => {
    pdf.addPage();
    y = margin;
    pdf.setFont('helvetica', 'normal');
  };

  const ensureSpace = (lineCount = 1) => {
    if (y + lineCount * lineHeight > bottom) addPage();
  };

  const wrappedLines = (value, fallback = 'Not available') => {
    const paragraphs = pdfText(value, fallback).split('\n');
    const lines = [];
    paragraphs.forEach((paragraph) => {
      if (!paragraph) {
        lines.push('');
        return;
      }
      lines.push(...pdf.splitTextToSize(paragraph, contentWidth));
    });
    return lines.length ? lines : [''];
  };

  const drawLines = (lines, color = [35, 45, 55], fontSize = 9) => {
    pdf.setTextColor(...color);
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(fontSize);
    lines.forEach((line) => {
      ensureSpace();
      if (line) pdf.text(line, margin, y);
      y += lineHeight;
    });
  };

  const drawHeading = (heading) => {
    pdf.setTextColor(5, 150, 105);
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(12);
    pdf.text(heading, margin, y);
    y += 16;
  };

  const write = (heading, body, fallback = 'Not available', keepTogether = false) => {
    const lines = wrappedLines(body, fallback);
    if (keepTogether && lines.length < 50 && y + (1 + lines.length) * lineHeight > bottom) {
      addPage();
    } else {
      ensureSpace(1 + Math.min(lines.length, 6));
    }
    drawHeading(heading);
    drawLines(lines);
    y += 10;
  };

  const writeTriage = () => {
    const reasonLines = wrappedLines(analysis.triage?.reason);
    ensureSpace(3);
    drawHeading('Triage');
    drawLines(
      [
        `Severity: ${pdfText(text(analysis.triage?.severity))} | Priority: ${pdfText(text(analysis.triage?.priority))}`,
      ],
      severityColor(analysis.triage?.severity),
    );
    drawLines(reasonLines);
    y += 10;
  };

  pdf.setTextColor(5, 190, 133);
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(18);
  pdf.text('Creation of Intelligent Bug Diagnosis Platform', margin, y);
  y += 17;
  pdf.setFontSize(11);
  pdf.text('with Fix Recommendation Assistance', margin, y);
  y += 25;
  pdf.setTextColor(35, 45, 55);
  pdf.setFontSize(9);
  pdf.text(`Generated ${pdfText(date.toLocaleString())}`, margin, y);
  y += 22;

  write('Bug Report', bugReport);
  writeTriage();
  write(
    'Log Analysis',
    `Exception: ${pdfText(text(analysis.log_info?.exception))} | File: ${pdfText(text(analysis.log_info?.file))} | Line: ${pdfText(text(analysis.log_info?.line))}`,
  );
  write(
    'Root Cause',
    `${pdfText(text(analysis.root_cause?.root_cause))}\n${pdfText(text(analysis.root_cause?.explanation))}\nConfidence: ${pdfText(text(analysis.root_cause?.confidence))}`,
  );
  write(
    'Similar Historical Bugs',
    (analysis.similar_bugs || [])
      .slice(0, 3)
      .map(
        (bug) =>
          `${pdfText(bug.bug_id)} - ${pdfText(bug.title)} (${Math.round(Number(bug.similarity_score || 0) * 100)}% match)`,
      )
      .join('\n') || 'No matching historical bugs were returned.',
  );
  write(
    'Recommended Remediation',
    `${pdfText(text(analysis.remediation?.recommended_fix))}\n\nCode Suggestion:\n${pdfText(text(analysis.remediation?.code_suggestion, 'Code suggestion unavailable'))}\n\nFix Confidence: ${pdfText(text(analysis.remediation?.fix_confidence, 'Unavailable'))}\n\nSteps:\n${(analysis.remediation?.steps || []).map((step, index) => `${index + 1}. ${pdfText(step)}`).join('\n') || 'No steps returned.'}\n\nPrevention: ${pdfText(text(analysis.remediation?.prevention))}`,
  );
  const matchedIds = (analysis.similar_bugs || [])
    .slice(0, 3)
    .map((bug) => pdfText(bug.bug_id))
    .join(', ');
  write(
    'Overall Summary',
    `${pdfText(bugReport)}\n\nProbable root cause: ${pdfText(text(analysis.root_cause?.root_cause))}\nHistorical evidence: ${matchedIds || 'No sufficiently similar historical bug was found.'}\nSeverity/Priority: ${pdfText(text(analysis.triage?.severity))} / ${pdfText(text(analysis.triage?.priority))}\nRecommended fix: ${pdfText(text(analysis.remediation?.recommended_fix))}\nPrevention: ${pdfText(text(analysis.remediation?.prevention))}`,
    'Not available',
    true,
  );

  return pdf;
}

export function downloadAnalysisPdf(analysis, bugReport, date = new Date()) {
  const pdf = createAnalysisPdf(analysis, bugReport, date);
  pdf.save(`smart-bug-report-${date.toISOString().slice(0, 10)}.pdf`);
}
