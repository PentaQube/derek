import { defineComponent, onBeforeUnmount, onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/core/components/card/Card'
import StatCard from '@/core/components/card/StatCard'
import PageHeader from '@/core/components/header/PageHeader'
import Button from '@/core/components/button/Button'
import { Clock, Copy, FileQuestionMark, MapPin, Trophy, UserRound ,QrCode} from 'lucide-vue-next'
import { connectLiveSessionWs, type WsParticipant, type LiveSessionWsMessage } from '../ws'
import {
  GetSessionLeaderboardApi,
  StartSessionApi,
  TriggerQuestionApi,
  EndSessionApi,
} from '../service'
import { useSessionStore } from '@/modules/sessions/store'
import { useAuthStore } from '@/modules/auth/store'
import type { SessionStatus } from '@/modules/sessions/components/StatusTabs'
import {
  OrderType,
  SessionExpand,
  SessionQuestionExpand,
  SessionQuestionOrderBy,
} from '@/modules/sessions/types'
import { useQuestionStore } from '@/modules/question/store'
import { ANSWER_TYPES } from '@/modules/question/constants'
import StatusChip from '@/core/components/statusChip/StatusChip'
import QRCode from 'qrcode'

type QuestionStatus = 'idle' | 'triggered'
type AnswerCountMap = Record<string, number>

interface Participant {
  id: number
  participantId?: number
  rank?: number
  name: string
  email: string
  user_id?: number
  score?: number
  answeredCount?: number
  ready?: boolean
}

function removeDuplicate(list: Participant[], p: WsParticipant & { rank?: number }) {
  const keyId = Number((p as any)?.user_id ?? (p as any)?.id)
  if (!Number.isFinite(keyId) || keyId <= 0) return

  const next: Participant = {
    id: keyId,
    participantId: Number.isFinite(Number(p.id)) ? Number(p.id) : undefined,
    rank: Number.isFinite(Number((p as any)?.rank)) ? Number((p as any)?.rank) : undefined,
    user_id: Number.isFinite(Number(p.user_id)) ? Number(p.user_id) : undefined,
    name: p.name || 'Unknown',
    email: p.email || '-',
    score: Number.isFinite(Number((p as any)?.score)) ? Number((p as any)?.score) : undefined,
    answeredCount: Number.isFinite(Number((p as any)?.answeredCount))
      ? Number((p as any)?.answeredCount)
      : Number.isFinite(Number((p as any)?.answered))
        ? Number((p as any)?.answered)
        : undefined,
    ready: typeof (p as any)?.ready === 'boolean' ? Boolean((p as any)?.ready) : undefined,
  }

  const idx = list.findIndex((x) => x.id === keyId)
  if (idx === -1) list.push(next)
  else list[idx] = { ...list[idx], ...next }
}

export default defineComponent({
  name: 'LiveSession',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const toast = useToast()
    const sessionStore = useSessionStore()
    const authStore = useAuthStore()
    const questionStore = useQuestionStore()
    const currentPage = ref(1)
    const pageSize = ref(10)

    const statusCodeById = computed(() => {
      const map = new Map<number, string>()
      for (const status of sessionStore.sessionStatusList) {
        map.set(status.id, status.code)
      }
      return map
    })

    // const sessionId = computed(() => Number(route.params.id))
    const sessionId = ref()

    const currentSession = computed(() => {
      const list = sessionStore.sessionList
      const id = Number(sessionId.value)
      const byId = id ? list.find((s) => Number((s as any)?.id) === id) : undefined
      return byId ?? null
    })

    const sessionQuestionsList = computed(() => {
      const sid = Number(sessionId.value)
      const fromSessionQuestions = sessionStore.sessionQuestions
        .filter((sq: any) => Number(sq?.session_id) === sid)
        .map((sq: any) => sq?.question ?? sq)
        .filter((q: any) => q && Number.isFinite(Number(q?.id)))

      if (fromSessionQuestions.length) return fromSessionQuestions

      const q = (currentSession.value as any)?.questions
      return Array.isArray(q) ? q : []
    })

    const sessionName = computed(() => String((currentSession.value as any)?.name ?? '—'))
    const venue = computed(() => String((currentSession.value as any)?.venue ?? '—'))
    const totalQuestions = computed(() => sessionQuestionsList.value.length)

    const participants = ref<Participant[]>([])

    const participantsCount = computed(() => {
      const fromList = participants.value.length
      if (fromList > 0) return fromList
      const fromSession = Number((currentSession.value as any)?.participant_count)
      return Number.isFinite(fromSession) ? Math.max(0, fromSession) : 0
    })

    const TRIGGERED_QUESTIONS_KEY_PREFIX = 'live_session_triggered_questions_'

    const readTriggeredQuestionsFromStorage = (sid: number | null | undefined): number[] => {
      try {
        const id = Number(sid)
        if (!Number.isFinite(id) || id <= 0) return []
        const raw = window.sessionStorage.getItem(`${TRIGGERED_QUESTIONS_KEY_PREFIX}${id}`)
        if (!raw) return []
        const parsed = JSON.parse(raw)
        const arr = Array.isArray(parsed) ? parsed : []
        const uniq = new Set<number>()
        for (const v of arr) {
          const n = Number(v)
          if (Number.isFinite(n) && n > 0) uniq.add(n)
        }
        return Array.from(uniq)
      } catch {
        return []
      }
    }

    const writeTriggeredQuestionsToStorage = (sid: number | null | undefined, ids: number[]) => {
      try {
        const id = Number(sid)
        if (!Number.isFinite(id) || id <= 0) return
        const uniq = Array.from(
          new Set(
            (Array.isArray(ids) ? ids : [])
              .map((x) => Number(x))
              .filter((n) => Number.isFinite(n) && n > 0),
          ),
        )
        window.sessionStorage.setItem(
          `${TRIGGERED_QUESTIONS_KEY_PREFIX}${id}`,
          JSON.stringify(uniq),
        )
      } catch {
        // ignore
      }
    }

    const triggeredQuestionIds = ref<number[]>([])
    const isTriggered = (id: number) => {
      return triggeredQuestionIds.value.includes(id)
    }

    watch(
      sessionId,
      (sid) => {
        triggeredQuestionIds.value = readTriggeredQuestionsFromStorage(sid)
      },
      { immediate: true },
    )

    const activeTab = ref<'questions' | 'leaderboard'>('questions')

    const questions = computed(() => {
      return sessionQuestionsList.value.map((q: any, idx: number) => ({
        id: Number(q?.id),
        number: idx + 1,
        label: String(q?.title ?? `Question ${idx + 1}`),
        is_triggered: q.is_triggered,
      }))
    })

    const activeQuestionId = ref<number | null>(null)

    const isActiveQuestionAlreadyTriggered = computed(() => {
      const qid = Number(activeQuestionId.value)
      if (!Number.isFinite(qid) || qid <= 0) return false
      return triggeredQuestionIds.value.includes(qid)
    })

    const activeQuestionIndex = computed(() => {
      if (!activeQuestionId.value) return -1
      return questions.value.findIndex((q) => q.id === activeQuestionId.value)
    })

    const activeQuestionNumber = computed(() => {
      const idx = activeQuestionIndex.value
      return idx >= 0 ? idx + 1 : questions.value.length ? 1 : 0
    })

    const sessionStatusComputed = computed<SessionStatus | null>(() => {
      const raw = currentSession.value?.session_status

      // no status yet
      if (!raw) return null

      // case A: expanded object - prefer `code` if present, else fall back to `display_name`/`name`
      if (typeof raw === 'object') {
        const code = (raw as any).code
        if (typeof code === 'string') {
          const c = code.toLowerCase().trim()
          if (c === 'ongoing' || c === 'upcoming' || c === 'completed') return c as SessionStatus
        }

        const display = (raw as any).display_name ?? (raw as any).name
        if (typeof display === 'string') {
          const d = display.toLowerCase().trim()
          if (d === 'ongoing' || d === 'upcoming' || d === 'completed') return d as SessionStatus
        }

        return null
      }

      // case B: numeric id
      if (typeof raw === 'number') {
        const status = statusCodeById.value.get(raw)
        return (status as SessionStatus) || null
      }

      return null
    })

    // status sync with store -->
    const sessionStatus = ref<SessionStatus | null>(sessionStatusComputed.value ?? null)

    watch(
      sessionStatusComputed,
      (status) => {
        sessionStatus.value = status
      },
      { immediate: true },
    )
    const questionStatus = ref<QuestionStatus>('idle')
    const questionTimeTotalSeconds = ref(40)
    const questionTimeRemainingSeconds = ref(40)
    const answerCountsByQuestion = ref<Record<number, AnswerCountMap>>({})

    let countdownTimer: number | undefined

    const formatTime = (totalSeconds: number) => {
      const seconds = Math.max(0, Math.floor(totalSeconds))
      const mm = String(Math.floor(seconds / 60)).padStart(2, '0')
      const ss = String(seconds % 60).padStart(2, '0')
      return `${mm}:${ss}`
    }

    const duration = computed(() => {
      const totalMs = sessionQuestionsList.value.reduce((acc: number, q: any) => {
        const v = Number(q?.time_limit_ms)
        return acc + (Number.isFinite(v) ? v : 0)
      }, 0)
      return formatTime(Math.floor(totalMs / 1000))
    })

    const timeRemainingText = computed(() => formatTime(questionTimeRemainingSeconds.value))
    const timePercent = computed(() => {
      const total = Math.max(1, Number(questionTimeTotalSeconds.value) || 1)
      const remaining = Math.max(0, Number(questionTimeRemainingSeconds.value) || 0)
      return Math.min(100, Math.max(0, (remaining / total) * 100))
    })

    //* Fetch sessions based on current filters
    // list to retrive
    const fetchSessions = async (id: number) => {
      await sessionStore.ListSessions({
        filter: {
          // ...(statusId && { session_status_id: statusId }),
          ...(id && { session_id: id }),
        },
        pagination: {
          limit: pageSize.value,
          offset: (currentPage.value - 1) * pageSize.value,
        },
        order: {
          // order_by: SessionOrderBy.UpdatedAt,
          // order_type: OrderType.Desc,
        },
        expand: [SessionExpand.SessionQuestion, SessionExpand.SessionStatus],
      })

      if (id) {
        await sessionStore.ListSessionQuestions({
          filter: { session_id: id },
          order: {
            order_by: SessionQuestionOrderBy.Position,
            order_type: OrderType.Asc,
          },
          expand: [SessionQuestionExpand.Question],
        })
      }
    }

    const currentQuestionFromStore = computed(() => {
      const q = questionStore.question
      if (!q) return null
      return Number(q.id) === Number(activeQuestionId.value) ? q : null
    })

    const questionTimeLimitSeconds = computed(() => {
      const ms = Number(currentQuestionFromStore.value?.time_limit_ms)
      if (!Number.isFinite(ms) || ms <= 0) return null
      return Math.max(1, Math.floor(ms / 1000))
    })

    watch(
      questionTimeLimitSeconds,
      (nextSeconds) => {
        if (!nextSeconds) return

        questionTimeTotalSeconds.value = nextSeconds

        if (questionStatus.value !== 'triggered') {
          questionTimeRemainingSeconds.value = nextSeconds
        }
      },
      { immediate: true },
    )

    const answerType = computed(() => {
      const at = currentQuestionFromStore.value?.answer_type
      if (!at) return null

      if (typeof at === 'number') {
        return Object.values(ANSWER_TYPES).find((t) => t.id === at) ?? null
      }

      return {
        id: at.id,
        displayName: (at as any)?.display_name ?? (at as any)?.displayName,
        code: at.code,
      }
    })

    const isTextbox = computed(() => answerType.value?.code === ANSWER_TYPES.TEXTBOX.code)

    const currentQuestionText = computed(() => {
      const id = activeQuestionId.value
      const fromList = id
        ? sessionQuestionsList.value.find((q: any) => Number(q?.id) === Number(id))
        : undefined
      return String(
        currentQuestionFromStore.value?.title ??
          fromList?.title ??
          `Question ${activeQuestionNumber.value}`,
      )
    })

    const currentQuestionOptions = computed(() => {
      if (isTextbox.value) return [] as Array<{ id: string; label: string }>

      const options = currentQuestionFromStore.value?.options
      if (Array.isArray(options) && options.length > 0) {
        return options.map((opt, idx) => ({
          id: String(opt.id ?? idx),
          label: String(opt.option_text ?? `Option ${idx + 1}`),
        }))
      }

      return ['A', 'B', 'C', 'D'].map((key) => ({ id: key, label: `Option ${key}` }))
    })

    const currentAnswerCounts = computed(() => {
      const qid = activeQuestionId.value
      if (!qid) {
        return {} as AnswerCountMap
      }
      return answerCountsByQuestion.value[qid] ?? ({} as AnswerCountMap)
    })

    const stopCountdown = () => {
      if (countdownTimer !== undefined) {
        window.clearInterval(countdownTimer)
        countdownTimer = undefined
      }
    }

    const resetQuestionState = () => {
      stopCountdown()
      questionStatus.value = 'idle'
      questionTimeRemainingSeconds.value = questionTimeTotalSeconds.value
    }

    const applyAnswerOptionCounts = (payload: any) => {
      const qid = Number(payload?.question_id)
      if (!Number.isFinite(qid) || qid <= 0) return

      const items = Array.isArray(payload?.items) ? payload.items : []
      const next: AnswerCountMap = {}

      for (const it of items) {
        const optionId = String(it?.option_id ?? '')
        const count = Number(it?.count)
        if (!optionId) continue
        next[optionId] = Number.isFinite(count) ? Math.max(0, Math.floor(count)) : 0
      }

      answerCountsByQuestion.value = {
        ...answerCountsByQuestion.value,
        [qid]: next,
      }
    }

    const handleTriggerQuestion = async () => {
      if (participantsCount.value === 0) return
      if (!activeQuestionId.value) return

      if (isActiveQuestionAlreadyTriggered.value) return

      // send trigger to backend; start countdown only on success
      try {
        const sid = Number(sessionId.value)
        const qid = Number(activeQuestionId.value)
        const res = await TriggerQuestionApi(sid, qid)
        if (res.status !== 'success') {
          toast.error(res.message || 'Failed to trigger question')
          return
        }

        if (!triggeredQuestionIds.value.includes(qid)) {
          triggeredQuestionIds.value = [...triggeredQuestionIds.value, qid]
          writeTriggeredQuestionsToStorage(sid, triggeredQuestionIds.value)
        }
      } catch (e) {
        toast.error(e instanceof Error ? e.message : 'Failed to trigger question')
        return
      }

      questionStatus.value = 'triggered'
      questionTimeRemainingSeconds.value = questionTimeTotalSeconds.value

      void hydrateParticipantsFromLeaderboard()

      stopCountdown()
      countdownTimer = window.setInterval(() => {
        questionTimeRemainingSeconds.value = Math.max(0, questionTimeRemainingSeconds.value - 1)
        if (questionTimeRemainingSeconds.value <= 0) {
          stopCountdown()
          questionStatus.value = 'idle'
        }
      }, 1000)
    }

    const handleNextQuestion = () => {
      const list = questions.value
      if (list.length === 0) return

      const idx = activeQuestionIndex.value
      const nextIdx = Math.min(list.length - 1, Math.max(0, idx) + 1)
      activeQuestionId.value = list[nextIdx]?.id ?? list[0]?.id ?? null
      resetQuestionState()
    }

    watch(activeQuestionId, async (nextId) => {
      resetQuestionState()
      if (nextId) await questionStore.GetQuestion(nextId)
    })

    watch(
      sessionQuestionsList,
      (next) => {
        if (!Array.isArray(next) || next.length === 0) {
          activeQuestionId.value = null
          return
        }

        const hasActive =
          activeQuestionId.value && next.some((q: any) => Number(q?.id) === activeQuestionId.value)

        if (!hasActive) {
          activeQuestionId.value = Number((next[0] as any)?.id)
        }
      },
      { immediate: true },
    )

    const hasRankingData = computed(() =>
      participants.value.some(
        (p) =>
          (p.score !== undefined && p.score !== null) ||
          (p.answeredCount !== undefined && p.answeredCount !== null),
      ),
    )

    const leaderboard = computed(() => {
      return [...participants.value].sort((a, b) => {
        const rankA = Number(a.rank)
        const rankB = Number(b.rank)
        const hasRankA = Number.isFinite(rankA) && rankA > 0
        const hasRankB = Number.isFinite(rankB) && rankB > 0

        // Prefer backend rank when available to keep UI consistent with leaderboard API.
        if (hasRankA && hasRankB && rankA !== rankB) return rankA - rankB
        if (hasRankA && !hasRankB) return -1
        if (!hasRankA && hasRankB) return 1

        const scoreDiff = (Number(b.score) || 0) - (Number(a.score) || 0)
        if (scoreDiff !== 0) return scoreDiff

        const answeredDiff = (Number(b.answeredCount) || 0) - (Number(a.answeredCount) || 0)
        if (answeredDiff !== 0) return answeredDiff

        return String(a.name).localeCompare(String(b.name))
      })
    })

    let socketCloser: null | (() => void) = null

    const hydrateParticipantsFromLeaderboard = async () => {
      const sid = Number(sessionId.value)
      if (!Number.isFinite(sid) || sid <= 0) return

      try {
        const res = await GetSessionLeaderboardApi(sid)
        const data = (res as any)?.data
        const items = Array.isArray(data?.items) ? data.items : []
        if (!items.length) return

        const next = items
          .map((it: any) => {
            const userId = Number(it?.user_id)
            if (!Number.isFinite(userId)) return null

            const rawName = String(it?.name ?? 'Unknown')
            const looksLikeEmail = rawName.includes('@')

            const name = looksLikeEmail ? rawName.split('@')[0] || rawName : rawName
            const email = looksLikeEmail ? rawName : String(it?.email ?? '-')

            return {
              id: userId,
              rank: Number.isFinite(Number(it?.rank)) ? Number(it?.rank) : undefined,
              user_id: userId,
              name,
              email,
              score: Number.isFinite(Number(it?.score)) ? Number(it?.score) : 0,
              answeredCount: Number.isFinite(Number(it?.answeredCount))
                ? Number(it?.answeredCount)
                : Number.isFinite(Number(it?.answered))
                  ? Number(it?.answered)
                  : undefined,
              ready: typeof it?.ready === 'boolean' ? Boolean(it?.ready) : undefined,
            } satisfies Participant
          })
          .filter(Boolean) as Participant[]

        if (!next.length) return

        // Merge with any existing WS-fed list, preferring freshest fields.
        const merged: Participant[] = [...participants.value]
        for (const p of next) {
          removeDuplicate(merged, {
            id: p.id,
            rank: p.rank,
            user_id: p.user_id ?? p.id,
            name: p.name,
            email: p.email,
            score: p.score,
            answeredCount: p.answeredCount,
            ready: p.ready,
          })
        }
        participants.value = merged
      } catch {
        // ignore: WS may still populate live list
      }
    }

    const connect = () => {
      if (!sessionId.value) return
      // close previous
      socketCloser?.() // prevent duplicates
      socketCloser = null

      const { close } = connectLiveSessionWs(
        sessionId.value,
        {
          // -> extravt cleamup
          onOpen: () => console.log('WS connected ✅'),
          onClose: () => console.log('WS closed ❌'),
          onError: (e) => console.log('WS error: ⚠️', e),
          onMessage: (msg: LiveSessionWsMessage) => {
            console.log('🚀 ~ connect ~ msg:', msg)
            //  handling payload
            if ((msg as any)?.type === 'participant_joined') {
              const m = msg as any
              if (m?.participant) removeDuplicate(participants.value, m.participant)
              return
            }

            // optional: support full list payload if backend sends it
            // console.log('🚀 ~ connect ~ msg:', msg)
            if ((msg as any)?.type === 'participants_list') {
              const m = msg as any
              if (Array.isArray(m?.participants)) {
                participants.value = []
                m.participants.forEach((p: WsParticipant) => removeDuplicate(participants.value, p))
              }
              return
            }

            if ((msg as any)?.type === 'leaderboard_updated') {
              const m = msg as any
              const items = Array.isArray(m?.items) ? m.items : []
              if (items.length) {
                for (const it of items) {
                  const userId = Number(it?.user_id)
                  if (!Number.isFinite(userId) || userId <= 0) continue

                  removeDuplicate(participants.value, {
                    id: userId,
                    rank: Number.isFinite(Number(it?.rank)) ? Number(it?.rank) : undefined,
                    user_id: userId,
                    name: typeof it?.name === 'string' ? it.name : null,
                    email: it.email,
                    score: it?.score,
                    answeredCount: it?.answeredCount ?? it?.answered,
                  })
                }
              }

              return
            }

            if ((msg as any)?.type === 'answer_option_counts') {
              const m = msg as any
              applyAnswerOptionCounts(m)
              return
            }
            // For reference only no
            if ((msg as any)?.type === 'participant_left') {
              const m = msg as any
              const pid = Number(m?.participant_id)
              if (Number.isFinite(pid)) {
                participants.value = participants.value.filter(
                  (p) => p.participantId !== pid && p.id !== pid && p.user_id !== pid,
                )
              }
              return
            }

            // console.log('WS message:', msg)
          },
        },
        authStore.token,
      )

      socketCloser = () => close()
    }

    const handleCopy = async () => {
      const url = `${window.location.origin}/#/session/${route.params.id}/join`

      try {
        await navigator.clipboard.writeText(url)
        toast.success(`Link copied:${url}`)
      } catch (error) {
        toast.error('Failed to copy' + error)
      }
    }

    const downloadQrSvg = async () => {
      const url = `${window.location.origin}/#/session/${route.params.id}/join`
      const svg = await QRCode.toString(url, {
        type: 'svg',
      })

      const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
      const objectUrl = URL.createObjectURL(blob)

      const a = document.createElement('a')
      a.href = objectUrl
      a.download = `session-${sessionName.value}.svg`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(objectUrl)
    }

    // onMounted(connect)
    // watch(sessionId, connect, { immediate: true }) //Todo -> //^ moved to onMount test and remove

    onBeforeUnmount(() => {
      socketCloser?.()
      socketCloser = null
      stopCountdown()
    })

    const handleStartSession = async () => {
      if (!sessionId.value) {
        toast.error(`Invalid session ID: ${sessionId.value}`)
        return
      }

      try {
        await StartSessionApi(sessionId.value)
        sessionStatus.value = 'ongoing'
        toast.success('Session started')
      } catch {
        toast.error('Failed to start session')
      }
    }

    const handleEndSession = async () => {
      try {
        console.log('Ending session...')

        await EndSessionApi(sessionId.value)

        sessionStatus.value = 'completed'

        if (sessionId.value) {
          router.push({ name: 'LeaderBoard', params: { id: sessionId.value } })
        }
      } catch (err) {
        console.error('Failed to end session', err)
      }
    }

    // * load questions
    onMounted(async () => {
      const id = Number(route.params.id)

      if (!id) {
        console.warn('No session id in route')
        toast.warning('No session id found')
        return
      }

      sessionId.value = id
      await fetchSessions(id)
      await hydrateParticipantsFromLeaderboard()
      connect()
    })

    return () => (
      <div class="p-8 max-w-7xl mx-auto">
        <PageHeader title="Live Session" description="Manage your live session" />

        <div class="mb-8">
          <Card className="mb-6">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h1 class="text-3xl font-bold text-gray-900 mb-2">{sessionName.value}</h1>
                <StatusChip
                  status={
                    (sessionStatus.value ?? undefined) as
                      | 'ongoing'
                      | 'upcoming'
                      | 'completed'
                      | undefined
                  }
                />
                <div class="flex items-center gap-1 text-gray-500">
                  <MapPin class="w-4 h-4" />
                  <span>Venue — {venue.value}</span>
                </div>
              </div>
              <div class="flex justify-end gap-4">
                {sessionStatus.value !== 'completed' && (
                  <Button
                    variant="ghost"
                    size="md"
                    onClick={handleCopy}
                    icon={() => <Copy class="h-4 w-4" />}
                    iconPosition="left"
                  >
                    Copy Links
                  </Button>
                )}
                {sessionStatus.value !== 'completed' && (
                  <button
                    onClick={downloadQrSvg}
                    class="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition"
                  >
                    <QrCode size={16} />
                      QR Code
                  </button>
                )}
                {sessionStatus.value === 'upcoming' && (
                  <Button variant="primary" size="md" onClick={handleStartSession}>
                    Start Session
                  </Button>
                )}
                {sessionStatus.value === 'ongoing' && (
                  <Button variant="danger" size="md" onClick={handleEndSession}>
                    End Session
                  </Button>
                )}
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
              <StatCard
                title="Duration"
                value={duration.value}
                icon={<Clock />}
                iconBoxColor="var(--color-secondary-50)"
                iconColor="var(--color-secondary-700)"
                useIconColorForText
                className="border-secondary-200"
              />

              <StatCard
                title="Questions"
                value={totalQuestions.value}
                icon={<FileQuestionMark />}
                iconBoxColor="var(--color-success-50)"
                iconColor="var(--color-success-700)"
                useIconColorForText
                className="border-success-200"
              />
              <StatCard
                title="Particpants"
                value={participantsCount.value}
                icon={<UserRound />}
                iconBoxColor="var(--color-primary-50)"
                iconColor="var(--color-primary-700)"
                useIconColorForText
                className="border-primary-200"
              />
            </div>
          </Card>

          <div class="grid grid-cols-2 gap-4"></div>
        </div>

        <div class="flex flex-col lg:flex-row gap-6">
          <Card className="mb-8 w-full lg:w-95">
            <div class="flex items-center justify-between border-b border-neutral-200 -mx-4 sm:-mx-5 px-4 sm:px-5 pb-3 mb-4">
              <div class="flex items-center gap-6">
                <button
                  class={[
                    'text-sm font-semibold pb-2',
                    activeTab.value === 'questions'
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-text-secondary',
                  ].join(' ')}
                  onClick={() => (activeTab.value = 'questions')}
                >
                  All Questions
                </button>
                <button
                  class={[
                    'text-sm font-semibold pb-2',
                    activeTab.value === 'leaderboard'
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-text-secondary',
                  ].join(' ')}
                  onClick={() => (activeTab.value = 'leaderboard')}
                >
                  Leaderboard({participantsCount.value})
                </button>
              </div>

              {/* <div class="text-sm text-text-secondary">
                Participants: {participants.value.length}
              </div> */}
            </div>

            {activeTab.value === 'questions' ? (
              <div class="space-y-2 max-h-100 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-300">
                {questions.value.length === 0 ? (
                  <div class="text-center py-8 text-gray-500">
                    <p>No questions yet</p>
                  </div>
                ) : (
                  questions.value.map((q, idx) => (
                    <button
                      key={q.id}
                      class={[
                        'w-full text-left rounded-lg border p-3 flex items-center gap-3',
                        isTriggered(q.id) || q.is_triggered
                          ? 'bg-gray-100 border-gray-200 text-gray-400'
                          : activeQuestionId.value === q.id
                            ? 'bg-primary-50 border-primary-200'
                            : 'bg-white border-neutral-200 hover:border-neutral-300',
                      ].join(' ')}
                      onClick={() => {
                        activeQuestionId.value = q.id
                      }}
                    >
                      <span class="text-xs font-semibold text-text-secondary w-10">
                        Q{idx + 1}:
                      </span>
                      <span class="font-medium text-text-primary truncate">{q.label}</span>
                    </button>
                  ))
                )}
              </div>
            ) : (
              <div class="space-y-3 max-h-100 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-300">
                {participants.value.length === 0 ? (
                  <div class="text-center py-8 text-gray-500">
                    <p>No participants yet</p>
                    <p class="text-sm mt-1">Share the session code to invite participants</p>
                  </div>
                ) : (
                  leaderboard.value.map((participant, idx) => {
                    const rank =
                      Number.isFinite(Number(participant.rank)) && Number(participant.rank) > 0
                        ? Number(participant.rank)
                        : idx + 1
                    const score = Number(participant.score) || 0
                    const _answered = Number(participant.answeredCount) || 0

                    const showTrophy = hasRankingData.value && rank <= 3

                    const trophyStyle =
                      rank === 1
                        ? { color: 'var(--color-warning-500)' }
                        : rank === 2
                          ? { color: 'var(--color-neutral-500)' }
                          : rank === 3
                            ? { color: 'var(--color-warning-700)' }
                            : undefined

                    return (
                      <div
                        key={participant.id}
                        class="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200"
                      >
                        <div class="flex items-center gap-4 min-w-0">
                          <div class="w-10 flex items-center justify-center">
                            {showTrophy ? (
                              <Trophy class="w-5 h-5" style={trophyStyle} />
                            ) : (
                              <span class="text-sm font-semibold text-text-secondary">{rank}</span>
                            )}
                          </div>

                          <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                            <span class="text-blue-600 font-semibold text-sm">
                              {(participant.name?.charAt(0) || 'U').toUpperCase()}
                            </span>
                          </div>

                          <div class="min-w-0">
                            <p class="font-medium text-gray-900 truncate">{participant.name}</p>
                            <p class="text-sm text-gray-500 truncate">{participant.email}</p>
                          </div>
                        </div>

                        <div class="text-right">
                          {!hasRankingData.value ? (
                            <span class="px-3 py-1 rounded-full text-xs font-medium text-green-600 bg-green-50">
                              ready
                            </span>
                          ) : (
                            <div>
                              <div class="text-sm font-semibold text-text-primary">{score}pts</div>
                              {/* <div class="text-xs text-text-secondary">({answered} answered)</div> */}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            )}
          </Card>
          {/* Question trigger section */}
          <Card className="mb-8 w-full lg:flex-1">
            <div class="flex items-start justify-between gap-4">
              <div>
                <div class="text-sm font-semibold text-text-primary">
                  Question {activeQuestionNumber.value} of {totalQuestions.value}
                </div>
                <div class="text-2xl font-bold text-text-primary mt-2">
                  {currentQuestionText.value}
                </div>
              </div>

              <div class="flex items-center gap-3">
                <div class="text-sm text-text-secondary flex items-center gap-2">
                  <Clock class="w-4 h-4" />
                  <span class="font-semibold text-text-primary font-mono">{timeRemainingText.value}</span>
                </div>
                <span
                  class={[
                    'px-3 py-1 rounded-full text-xs font-semibold',
                    questionStatus.value === 'triggered' || isActiveQuestionAlreadyTriggered.value
                      ? 'text-green-700 bg-green-50'
                      : 'text-gray-600 bg-gray-100',
                  ].join(' ')}
                >
                  {questionStatus.value === 'triggered'
                    ? 'Active'
                    : isActiveQuestionAlreadyTriggered.value
                      ? 'Triggered'
                      : 'Idle'}
                </span>
              </div>
            </div>

            {questionStatus.value === 'triggered' ? (
              <div class="mt-6">
                <div class="flex items-center justify-between text-sm text-text-secondary mb-2">
                  <span>Time Remaining</span>
                  <span class="font-semibold text-text-primary font-mono">{timeRemainingText.value}</span>
                </div>
                <div class="h-2 rounded-full bg-neutral-200 overflow-hidden">
                  <div class="h-full bg-green-500" style={{ width: `${timePercent.value}%` }}></div>
                </div>
              </div>
            ) : null}

            {isTextbox.value ? (
              <div class="mt-8 rounded-lg border border-neutral-200 bg-white p-4">
                <div class="text-sm text-text-secondary">Responses</div>
                <div class="text-lg font-semibold text-text-primary mt-1">
                  {Object.values(currentAnswerCounts.value).reduce((sum, v) => sum + (v || 0), 0)}{' '}
                  people
                </div>
              </div>
            ) : (
              <div class="grid grid-cols-1 gap-4 mt-8">
                {currentQuestionOptions.value.map((opt, idx) => (
                  <div
                    key={opt.id}
                    class="rounded-lg border border-neutral-200 bg-white p-4 flex items-start gap-3"
                  >
                    <div class="w-9 h-9 rounded-lg bg-neutral-900 text-white flex items-center justify-center font-bold text-sm shrink-0">
                      {String.fromCharCode(65 + idx)}
                    </div>
                    <div class="min-w-0">
                      <div class="font-medium text-text-primary break-words whitespace-normal">{opt.label}</div>
                      <div class="text-sm text-green-600 mt-1">
                        {currentAnswerCounts.value[opt.id] ?? 0} people
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div class="flex items-center gap-3 mt-8">
              <Button
                variant="primary"
                size="lg"
                onClick={handleTriggerQuestion}
                disabled={
                  participantsCount.value === 0 ||
                  questionStatus.value === 'triggered' ||
                  isActiveQuestionAlreadyTriggered.value ||
                  questions.value[activeQuestionIndex.value]?.is_triggered
                }
              >
                Trigger Question
              </Button>

              <Button variant="outline" size="lg" onClick={handleNextQuestion}>
                Next Question
              </Button>
            </div>
          </Card>
        </div>
      </div>
    )
  },
})
