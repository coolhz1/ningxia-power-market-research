"use strict";

const chapters = [...document.querySelectorAll(".chapter")];
const nav = document.querySelector(".toc");
const navLinks = new Map([...nav.querySelectorAll("a")].map(link => [link.hash.slice(1), link]));
const mobile = window.matchMedia("(max-width: 780px)");
if (mobile.matches) nav.open = false;
nav.addEventListener("click", event => {
  if (mobile.matches && event.target.closest("a")) nav.open = false;
});

if ("IntersectionObserver" in window) {
  const visible = new Set();
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) visible.add(entry.target);
      else visible.delete(entry.target);
    }
    const active = chapters.find(section => visible.has(section));
    for (const [id, link] of navLinks) {
      if (id === active?.id) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    }
  }, {rootMargin: "-15% 0px -55% 0px"});
  chapters.forEach(chapter => observer.observe(chapter));
}

const search = document.querySelector("#report-search");
const results = document.querySelector("#search-results");
const searchable = [
  ...chapters.map(chapter => ({
    id: chapter.id,
    title: chapter.querySelector("h2").textContent,
    text: chapter.textContent.toLowerCase()
  })),
  ...Array.from(document.querySelectorAll(".source"), source => ({
    id: source.id,
    title: source.querySelector("a").textContent,
    text: source.textContent.toLowerCase()
  }))
];
search.closest(".search").hidden = false;
search.addEventListener("input", () => {
  const terms = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  results.replaceChildren();
  if (!terms.length) return;
  const matches = searchable.filter(item => terms.every(term => item.text.includes(term)));
  const top = matches.filter(item => terms.every(term => item.title.toLowerCase().includes(term)));
  const selected = [...new Set([...top, ...matches])].slice(0, 12);
  const count = document.createElement("p");
  count.textContent = matches.length ? `找到 ${matches.length} 条结果${matches.length > selected.length ? "，显示前 12 条" : ""}` : "未找到匹配项";
  results.append(count);
  if (!selected.length) return;
  const list = document.createElement("ol");
  for (const match of selected) {
    const row = document.createElement("li");
    const link = document.createElement("a");
    link.href = "#" + match.id;
    link.textContent = match.title;
    row.append(link);
    list.append(row);
  }
  results.append(list);
});
search.addEventListener("keydown", event => {
  if (event.key === "Escape") {
    search.value = "";
    results.replaceChildren();
  }
});

const copyButton = document.querySelector(".copy");
if (navigator.clipboard?.writeText) {
  copyButton.hidden = false;
  copyButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(copyButton.nextElementSibling.textContent);
      copyButton.textContent = "已复制";
    } catch {
      copyButton.textContent = "请手动复制";
    }
    window.setTimeout(() => { copyButton.textContent = "复制伪代码"; }, 1500);
  });
}

const form = document.querySelector("#settlement-form");
const money = new Intl.NumberFormat("zh-CN", {maximumFractionDigits: 2});
const outputs = ["cost", "revenue", "net"].map(id => document.getElementById(id));
const status = document.getElementById("calc-status");
const note = status.textContent;
form.closest(".calculator").hidden = false;

function calculate() {
  const names = ["charge", "chargePrice", "discharge", "dischargePrice"];
  const inputs = names.map(name => form.elements.namedItem(name));
  const [charge, chargePrice, discharge, dischargePrice] = inputs.map(input => input.valueAsNumber);
  const cost = 12 * 100 + (charge - 12) * chargePrice;
  const revenue = 10 * 500 + (discharge - 10) * dischargePrice;
  const values = [cost, revenue, revenue - cost];
  const valid = inputs.every(input => input.validity.valid) && values.every(Number.isFinite);
  outputs.forEach((output, i) => {
    output.value = valid ? money.format(Math.round((values[i] + Number.EPSILON) * 100) / 100) + " 元" : "—";
  });
  status.textContent = valid ? note : "请输入有效数字。单时段计量电量范围为 0–15 MWh。";
}
form.addEventListener("input", calculate);
form.addEventListener("submit", event => event.preventDefault());
form.addEventListener("reset", () => window.requestAnimationFrame(calculate));
calculate();
