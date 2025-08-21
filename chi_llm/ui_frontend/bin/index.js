#!/usr/bin/env node
import React, {useEffect, useState} from 'react';
import {render, Box, Text, useInput} from 'ink';
import SelectInput from 'ink-select-input';
import {execFile} from 'node:child_process';

const e = React.createElement;

const runCli = (args) => new Promise((resolve) => {
  execFile('chi-llm', args, {encoding: 'utf8'}, (err, stdout, stderr) => {
    resolve({err, stdout, stderr});
  });
});

const useQuitKey = () => {
  useInput((input, key) => {
    if (input === 'q' || key.escape) {
      process.exit(0);
    }
  });
};

const ModelsScreen = ({onBack}) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    (async () => {
      const {stdout} = await runCli(['models', 'list', '--json']);
      try {
        const data = JSON.parse(stdout || '[]');
        const mapped = data.map((m) => ({
          label: `${m.current ? '★ ' : ''}${m.name} [${m.id}] ${m.downloaded ? '✓' : ''}`,
          value: m.id
        }));
        setItems(mapped);
      } catch (e) {
        setMsg('Failed to parse models list.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const onSelect = async (item) => {
    setMsg('Setting model...');
    const {stderr} = await runCli(['models', 'set', item.value, '--local']);
    setMsg(stderr ? stderr.trim() : 'Model set for this project.');
  };

  const children = [
    e(Text, {key: 'title', bold: true}, 'Models'),
    loading
      ? e(Text, {key: 'loading'}, 'Loading...')
      : (items.length > 0
          ? e(SelectInput, {key: 'list', items, onSelect})
          : e(Text, {key: 'empty'}, 'No models found.')
        ),
    msg ? e(Text, {key: 'msg', color: 'gray'}, msg) : null,
    e(Text, {key: 'hint'}, 'Press Esc to go back, q to quit.')
  ].filter(Boolean);

  return e(Box, {flexDirection: 'column'}, ...children);
};

const ConfigScreen = ({onBack}) => (
  e(Box, {flexDirection: 'column'},
    e(Text, {bold: true}, 'Config (coming soon)'),
    e(Text, {color: 'gray'}, 'Edit temperature, max_tokens and provider settings with live validation.'),
    e(Text, null, 'Press Esc to go back, q to quit.'),
  )
);

const Dashboard = () => {
  useQuitKey();
  const [screen, setScreen] = useState('menu');
  const items = [
    {label: 'Bootstrap', value: 'bootstrap'},
    {label: 'Models', value: 'models'},
    {label: 'Config', value: 'config'},
    {label: 'Quit', value: 'quit'}
  ];

  const onSelect = async (item) => {
    if (item.value === 'quit') process.exit(0);
    if (item.value === 'bootstrap') {
      await runCli(['bootstrap', '.']);
      return;
    }
    setScreen(item.value);
  };

  if (screen === 'models') return e(ModelsScreen, {onBack: () => setScreen('menu')});
  if (screen === 'config') return e(ConfigScreen, {onBack: () => setScreen('menu')});

  return e(Box, {flexDirection: 'column'},
    e(Text, {bold: true}, 'chi_llm Control Center'),
    e(Text, {color: 'gray'}, 'Use arrows/enter to navigate. q/Esc to exit.'),
    e(Box, {marginTop: 1}, e(SelectInput, {items, onSelect}))
  );
};

render(e(Dashboard));
