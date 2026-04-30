import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const SIZES = [
  { value: 'tiny',   icon: '🐇', name: '5 минут',  parts: '3 части' },
  { value: 'small',  icon: '🦔', name: '10 минут', parts: '8 частей' },
  { value: 'medium', icon: '🐌', name: '20 минут', parts: '16 частей' },
  { value: 'large',  icon: '🏰', name: '40 минут', parts: '32 части' },
]

const HERO_MODES = [
  {
    value: 'profile_child',
    icon: '💡',
    title: 'Использовать ребёнка из профиля',
    text: 'Имя, возраст, пол и увлечения подтянутся автоматически.',
  },
  {
    value: 'random',
    icon: '🎲',
    title: 'Случайный герой',
    text: 'Сервис сам предложит персонажа для истории.',
  },
  {
    value: 'custom',
    icon: '✍🏻',
    title: 'Описать героя самостоятельно',
    text: 'Напишите, каким должен быть главный герой.',
  },
]

const GENRES = [
  'Случайный жанр', 'Волшебная сказка', 'Приключения', 'История про дружбу',
  'Сказка на ночь', 'Фэнтези', 'Сказка о животных', 'Притча', 'Другой',
]

const STATUS = {
  idle:      null,
  creating:  'Создаём сказку…',
  starting:  'Генерируем первую часть…',
}

export default function TaleCreatePage() {
  const nav = useNavigate()
  const { userId } = useAuth()

  const [form, setForm] = useState({
    name: '',
    hero_mode: 'profile_child',
    hero_description: '',
    genre: GENRES[0],
    moral: '',
    size: 'small',
  })
  const [phase, setPhase] = useState('idle')   // 'idle' | 'creating' | 'starting'
  const [error, setError] = useState('')

  const set = (k) => (v) => setForm(f => ({ ...f, [k]: v }))
  const loading = phase !== 'idle'

  async function handleCreate(e) {
    e.preventDefault()
    if (form.hero_mode === 'custom' && !form.hero_description.trim()) {
      return setError('Опишите главного героя или выберите ребёнка из профиля / случайного героя')
    }
    setError('')

    try {
      // 1. Создаём сказку
      setPhase('creating')
      await api.createTale(userId, {
        name: form.name.trim(),
        hero_mode: form.hero_mode,
        hero_description: form.hero_description.trim(),
        genre: form.genre,
        moral: form.moral.trim() || 'Случайная мораль',
        size: form.size,
      })

      // 2. Сразу отправляем стартовое сообщение — AI генерирует первую часть
      setPhase('starting')
      await api.addMessage(userId, 'Начни историю')

      // 3. Переходим в чат — первая часть уже готова
      nav('/tale')
    } catch (err) {
      setPhase('idle')
      if (err.message.toLowerCase().includes('профиль')) {
        nav('/profile')
      } else {
        setError(err.message)
      }
    }
  }

  return (
    <div className="page">
      <div className="card" style={{ maxWidth: 620 }}>
        <p className="brand">✦ Новая сказка ✦</p>
        <h2>Настроить историю</h2>
        <p className="subtitle">Давай настроим сказку под ребёнка: выберите героя, жанр, мораль и продолжительность.</p>

        {error && <div className="alert alert-error">{error}</div>}

        {/* Статус генерации */}
        {loading && (
          <div className="alert alert-warning" style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
            <span className="spinner" />
            {STATUS[phase]}
          </div>
        )}

        <form onSubmit={handleCreate}>
          <div className="field">
            <label>Главный герой истории</label>
            <p className="helper-text">Выберите ребёнка из профиля, доверьтесь случайному герою или опишите персонажа сами.</p>
            <div className="choice-grid">
              {HERO_MODES.map(mode => (
                <button
                  key={mode.value}
                  type="button"
                  className={`choice-card${form.hero_mode === mode.value ? ' selected' : ''}`}
                  onClick={() => !loading && set('hero_mode')(mode.value)}
                  disabled={loading}
                >
                  <span className="choice-icon">{mode.icon}</span>
                  <span className="choice-title">{mode.title}</span>
                  <span className="choice-text">{mode.text}</span>
                </button>
              ))}
            </div>
          </div>

          {form.hero_mode === 'custom' && (
            <div className="field">
              <label>Описание героя</label>
              <textarea
                value={form.hero_description}
                onChange={e => set('hero_description')(e.target.value)}
                placeholder="Например: маленький дракон, который любит звёзды и боится темноты"
                maxLength={500}
                disabled={loading}
              />
              <p className="helper-text">Можно описать характер, интересы, внешность или мечту героя — так сказка получится живее.</p>
            </div>
          )}

          <div className="field">
            <label>Жанр</label>
            <select value={form.genre} onChange={e => set('genre')(e.target.value)} disabled={loading}>
              {GENRES.map(g => <option key={g} value={g}>{g}</option>)}
            </select>
            <p className="helper-text">Например: волшебная сказка, приключение, история про дружбу, сказка на ночь.</p>
          </div>

          <div className="field">
            <label>Мораль</label>
            <textarea
              value={form.moral}
              onChange={e => set('moral')(e.target.value)}
              placeholder="Чему должна научить сказка? Например: быть добрым, не бояться трудностей, помогать друзьям"
              maxLength={500}
              disabled={loading}
            />
            <p className="helper-text">Можно оставить поле пустым — тогда мораль будет случайной, как в Telegram-боте.</p>
          </div>

          <div className="field">
            <label>Продолжительность</label>
            <p className="helper-text">Выберите короткую сказку на 3–5 минут или более длинную историю для чтения перед сном.</p>
            <div className="size-grid">
              {SIZES.map(s => (
                <div
                  key={s.value}
                  className={`size-card${form.size === s.value ? ' selected' : ''}${loading ? ' disabled' : ''}`}
                  onClick={() => !loading && set('size')(s.value)}
                  style={loading ? { pointerEvents: 'none', opacity: .5 } : {}}
                >
                  <span className="size-icon">{s.icon}</span>
                  <span className="size-name">{s.name}</span>
                  <span className="size-parts">{s.parts}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="field">
            <label>Название или тема</label>
            <input
              type="text" value={form.name}
              onChange={e => set('name')(e.target.value)}
              placeholder="Необязательно: например, Тайна лунного леса" maxLength={100}
              disabled={loading}
            />
            <p className="helper-text">Если оставить поле пустым, сервис сам подберёт тему по выбранным настройкам.</p>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ marginTop: '.5rem' }}
            disabled={loading}
          >
            {loading
              ? <><span className="spinner" /> {STATUS[phase]}</>
              : '✦ Создать сказку'}
          </button>
        </form>

        <div className="orn">✦</div>
        <button className="btn btn-ghost" onClick={() => nav('/profile')} disabled={loading}>
          ← Назад в профиль ребёнка
        </button>
      </div>
    </div>
  )
}
