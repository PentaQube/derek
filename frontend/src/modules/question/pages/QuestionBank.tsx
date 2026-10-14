import DataTable from '@/core/components/dataTable/DataTable'
import Button from '@/core/components/button/Button'
import AddBankModal from '../components/AddBankModal'
import AddQuestionModal from '../components/AddQuestionModal'
import {
  CreateQBApi,
  DeleteQBApi,
  EditQBApi,
  CreateNewQuestionAPI,
  UpdateQuestionAPI,
  DeleteQuestionAPI,
} from '../service'
import type { QuestionBank, Question, CreateQuestion } from '../types'
import { ANSWER_TYPES, type AnswerTypeKey } from '../constants'
import { Pencil, Search, Trash } from 'lucide-vue-next'
import DeleteConfirmModal from '@/core/components/modals/DeleteConfirmModal'
import { useToast } from '@/core/composables/useToast'
import { useQuestionStore } from '../store'
import { storeToRefs } from 'pinia'

export default defineComponent({
  setup() {
    const toast = useToast()
    const questionStore = useQuestionStore()
    const communityStore = useCommunityStore()

    // Use store state with storeToRefs for reactivity
    const { questionBanks, error } = storeToRefs(questionStore) //Todo :loading

    // Pagination state for banks
    const page = ref(1)
    const pageSize = ref(10)
    const selectedBankId = ref<number | null>(null)
    const selectedBank = computed(() => {
      return banks.value.find((b: QuestionBank) => b.id === selectedBankId.value)
    })

    // Pagination and search state for questions
    const questionPage = ref(1)
    const questionPageSize = ref(10)
    const questionSearch = ref('')
    const questionTotalCount = ref(0)

    const showAddBankModal = ref(false)
    const showAddQuestionModal = ref(false)
    const showDeleteConfirmModal = ref(false)
    const bankIdToDelete = ref<number | null>(null)
    const editingBank = ref<QuestionBank | null>(null)
    const editingQuestion = ref<Question | null>(null)

    // Computed banks from store
    const banks = computed(() => questionBanks.value?.items || [])

    // Questions per bank (loaded separately)
    const bankQuestions = ref<Record<number, Question[]>>({})
    const loadingQuestions = ref(false)
    const questionsError = ref<string | null>(null)

    // Initial load
    onMounted(async () => {
      await loadBanks({ page: page.value, pageSize: pageSize.value })
    })

    // Reload banks when community changes
    watch(
      () => communityStore.communityId,
      async (next, prev) => {
        if (next === prev) return
        await loadBanks({ page: page.value, pageSize: pageSize.value })
      },
    )

    // *  LIST BANKS - Use store action
    const loadBanks = async (params?: { page?: number; pageSize?: number }) => {
      if (!communityStore.communityId) return

      try {
        await questionStore.QBList({
          order_by: 'updated_at',
          order_type: 'desc',
          ...params,
        })
      } catch (err: any) {
        const errorMessage = error.value || err?.message || 'Failed to load banks'
        toast.error(errorMessage)
        console.error('Failed to load banks', err)
      }
    }

    //&                            EDIT BANK                             */

    //< Handle Edit
    const onEditClick = (bankId: number) => {
      const bank = banks.value.find((b: QuestionBank) => b.id === bankId)
      if (bank) {
        editingBank.value = bank
        showAddBankModal.value = true
      }
    }
    // > Update Question Bank
    const handleUpdateBank = async (id: number, data: { name: string; description: string }) => {
      try {
        const response = await EditQBApi(id, {
          name: data.name,
          description: data.description.trim() || null,
        })

        if (response.code === 200) {
          await questionStore.QBList()
          // Use server message if available
          toast.success(response.message || 'Question bank updated successfully')
        }

        showAddBankModal.value = false
        editingBank.value = null
      } catch (err: any) {
        const errorMessage = err?.message ?? String(err)
        toast.error(`Failed to update bank: ${errorMessage}`)
        console.error('Failed to update bank', err)
      }
    }

    //!                            DELETE BANK                             */

    //^ Toggle Warning !!!
    const toggleDeleteWarning = (bankId: number) => {
      bankIdToDelete.value = bankId
      showDeleteConfirmModal.value = true
    }

    // > Close Warning
    const closeDeleteModal = () => {
      showDeleteConfirmModal.value = false
      bankIdToDelete.value = null
    }

    // ! Confirm Deletion
    const confirmDeleteBank = async () => {
      if (bankIdToDelete.value === null) return

      await handleDeleteBank(bankIdToDelete.value)
      closeDeleteModal()
    }

    // ! Delete API
    const handleDeleteBank = async (bankId: number) => {
      try {
        const response = await DeleteQBApi(bankId)

        // Remove from questions
        delete bankQuestions.value[bankId]

        // Update selected bank if needed
        if (selectedBankId.value === bankId) {
          selectedBankId.value = banks.value.length ? (banks.value[0]?.id ?? null) : null
        }

        // Reload banks from store to keep in sync
        await questionStore.QBList()

        // Show server message or default
        toast.success(response.message || 'Question bank deleted successfully')
      } catch (err: any) {
        const errorMessage = err?.message ?? String(err)
        toast.error(`Failed to delete bank: ${errorMessage}`)
        console.error('Failed to delete bank', err)
      }
    }

    //*                            CREATE  BANK                            */

    // * Create Question Bank
    const handleCreateBank = async (data: { name: string; description: string }) => {
      try {
        const response = await CreateQBApi({
          name: data.name,
          description: data.description.trim() || null,
          community_id: communityStore?.communityId ? communityStore.communityId : 0, //TODO : zero to be removed
        })

        if (response.code === 200 || response.code === 201) {
          await questionStore.QBList()
          toast.success(response.message || 'Question bank created successfully')
        }

        showAddBankModal.value = false
        editingBank.value = null
      } catch (err: any) {
        const errorMessage = err?.message ?? String(err)
        toast.error(`Failed to create bank: ${errorMessage}`)
        console.error('Failed to create bank', err)
      }
    }
    //>                        QUESTION SECTION                         */
    const loadQuestions = async (
      bankId: number,
      params?: { page?: number; pageSize?: number; search?: string },
    ) => {
      if (!bankId) return

      loadingQuestions.value = true
      questionsError.value = null

      // Use provided params or current state
      const currentPage = params?.page ?? questionPage.value
      const currentPageSize = params?.pageSize ?? questionPageSize.value
      const currentSearch = params?.search ?? questionSearch.value

      try {
        const data = await questionStore.QuestionList({
          filter: {
            question_bank_id: bankId,
          },
          pagination: {
            limit: currentPageSize,
            offset: (currentPage - 1) * currentPageSize,
          },
          order: {
            order_by: 'id',
            order_type: 'asc',
          },
          search: currentSearch,
        })

        if (data?.items) {
          bankQuestions.value[bankId] = data.items
          questionTotalCount.value = data.total_count ?? 0
        }
      } catch (err: any) {
        const errorMessage = err?.message ?? String(err)
        questionsError.value = errorMessage
        toast.error(`Failed to load questions: ${errorMessage}`)
        console.error('❌ Failed to load questions:', err)
      } finally {
        loadingQuestions.value = false
      }
    }
    //
    const selectBank = (bankId: number) => {
      selectedBankId.value = bankId
      questionPage.value = 1
      questionSearch.value = ''
      loadQuestions(bankId)
    }

    const columns = [
      { key: 'title', label: 'Question', width: '10' },
      { key: 'total_score', label: 'Scored', align: 'center' as const },
      { key: 'time_limit_ms', label: 'Time (ms)', align: 'center' as const },
      // { key: 'is_scored', label: 'Scored', align: 'center' as const },
    ]

    //* Add new question
    const onAddNewQuestion = () => {
      showAddQuestionModal.value = true
    }

    const currentQuestions = computed(() => {
      if (!selectedBankId.value) return []
      return bankQuestions.value[selectedBankId.value] || []
    })

    const handleChange = (params: any) => {
      questionPage.value = params.page
      questionPageSize.value = params.pageSize ?? questionPageSize.value

      if (selectedBankId.value) {
        loadQuestions(selectedBankId.value, {
          page: questionPage.value,
          pageSize: questionPageSize.value,
        })
      }
    }

    /**
     * Handle search input changes
     * Resets to page 1 and reloads questions
     */
    const handleSearch = () => {
      if (selectedBankId.value) {
        questionPage.value = 1
        loadQuestions(selectedBankId.value, {
          page: 1,
          pageSize: questionPageSize.value,
          search: questionSearch.value,
        })
      }
    }

    const handleCreateQuestion = async (data: {
      question: string
      timeLimit: number
      answerType: AnswerTypeKey
      isScored: boolean
      options: Array<{ text: string; isCorrect: boolean; score: number }>
    }) => {
      if (!selectedBankId.value) {
        toast.error('Please select a question bank first')
        return
      }

      try {
        const invalidOption = data.options.find(
          (opt) => data.isScored && opt.isCorrect && !Number.isInteger(Number(opt.score)),
        )

        if (invalidOption) {
          const message = 'Option scores must be integer numbers'
          toast.error(message)
          throw new Error(message)
        }
        const createData: CreateQuestion = {
          question_bank_id: selectedBankId.value,
          title: data.question,
          time_limit_ms: data.timeLimit * 1000, // Convert seconds to milliseconds
          answer_type_id: ANSWER_TYPES[data.answerType].id,
          options: data.options.map((opt) => ({
            option_text: opt.text,
            score: data.isScored && opt.isCorrect ? opt.score : 0,
          })),
        }

        // Call API to create question
        const response = await CreateNewQuestionAPI(createData)

        // Check response code
        if (response.code === 200 || response.code === 201) {
          // Reload questions to show the new one
          await loadQuestions(selectedBankId.value, {
            page: questionPage.value,
            pageSize: questionPageSize.value,
          })

          toast.success(response.message || 'Question created successfully')
          showAddQuestionModal.value = false
        }
      } catch (err: any) {
        if (err?.response?.data?.errors?.length) {
          const validationErrors = err.response.data.errors

          validationErrors.forEach((error: any) => {
            const fieldPath = error.loc?.slice(1).join('.')
            toast.error(`${fieldPath}: ${error.msg}`)
          })
        } else {
          const errorMessage =
            err?.response?.data?.message || err?.message || 'Failed to create question'

          toast.error(errorMessage)
        }

        console.error('❌ Failed to create question:', err)

        throw err
      }
    }

    const handleUpdateQuestion = async (
      id: number,
      data: {
        question: string
        timeLimit: number
        answerType: AnswerTypeKey
        isScored: boolean
        options: Array<{
          id?: number
          text: string
          isCorrect: boolean
          score: number
        }>
      },
    ) => {
      if (!selectedBankId.value) {
        toast.error('Please select a question bank first')
        return
      }

      try {
        const invalidOption = data.options.find(
          (opt) => data.isScored && opt.isCorrect && !Number.isInteger(Number(opt.score)),
        )

        if (invalidOption) {
          const message = 'Option scores must be integer numbers'
          toast.error(message)
          throw new Error(message)
        }
        const updateData: CreateQuestion = {
          question_bank_id: selectedBankId.value,
          title: data.question,
          time_limit_ms: data.timeLimit * 1000, // Convert seconds to milliseconds
          answer_type_id: ANSWER_TYPES[data.answerType].id,
          options: data.options.map((opt) => ({
            id: opt.id,
            option_text: opt.text,
            score: data.isScored && opt.isCorrect ? opt.score : 0,
          })),
        }

        // Call API to update question
        const response = await UpdateQuestionAPI(id, updateData)

        // Check response code
        if (response.code === 200 || response.code === 201) {
          // Reload questions to show the updated one
          await loadQuestions(selectedBankId.value, {
            page: questionPage.value,
            pageSize: questionPageSize.value,
          })

          toast.success(response.message || 'Question updated successfully')
          showAddQuestionModal.value = false
          editingQuestion.value = null
        }
      } catch (err: any) {
        if (err?.response?.data?.errors?.length) {
          const validationErrors = err.response.data.errors

          validationErrors.forEach((error: any) => {
            const fieldPath = error.loc?.slice(1).join('.')
            toast.error(`${fieldPath}: ${error.msg}`)
          })
        } else {
          const errorMessage =
            err?.response?.data?.message || err?.message || 'Failed to update question'

          toast.error(errorMessage)
        }

        console.error('❌ Failed to update question:', err)

        throw err
      }
    }

    const handleEditQuestion = (row: Question) => {
      editingQuestion.value = row
      showAddQuestionModal.value = true
    }

    const handleDeleteQuestion = async (row: Question) => {
      if (!selectedBankId.value) return
      if (!row?.id) return

      try {
        const response = await DeleteQuestionAPI(row.id)

        if (response.status !== 'success' && response.code !== 200 && response.code !== 204) {
          toast.error(response.message || 'Failed to delete question')
          return
        }

        await loadQuestions(selectedBankId.value, {
          page: questionPage.value,
          pageSize: questionPageSize.value,
          search: questionSearch.value,
        })

        toast.success(response.message || 'Question deleted successfully')
      } catch (err: any) {
        const errorMessage = err?.message ?? String(err)
        toast.error(`Failed to delete question: ${errorMessage}`)
        console.error(' Failed to delete question:', err)
      }
    }

    return () => (
      <div class="min-h-screen bg-gray-50 p-6">
        <div class="mx-auto max-w-7xl">
          {/* Page Header */}
          <div class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900">Question Banks</h1>
            <p class="text-gray-600">Manage your question banks</p>
          </div>

          {/* Main Content */}
          <div class="grid grid-cols-12 gap-6">
            {/* Left Sidebar - Banks List */}
            <div class="col-span-3">
              <div class="rounded-2xl bg-white p-6 shadow-sm">
                <div class="mb-4 flex items-center justify-between">
                  <h2 class="text-lg font-semibold text-gray-900">Banks</h2>
                  <button
                    class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                    onClick={() => (showAddBankModal.value = true)}
                  >
                    + Bank
                  </button>
                </div>

                <div class="space-y-2">
                  {/* {loading.value && <p class="text-sm text-gray-500">Loading banks...</p>} */}
                  {error.value && <p class="text-sm text-red-500">{error.value}</p>}
                  {banks.value.map((bank: QuestionBank) => (
                    <div
                      key={bank.id}
                      class={`group cursor-pointer rounded-xl border-2 p-4 transition-all ${
                        selectedBankId.value === bank.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => selectBank(bank.id)}
                    >
                      <div class="flex items-start justify-between gap-4">
                        <div class="flex-1 min-w-0">
                          <h3
                            class={`font-semibold wrap-break-word ${
                              selectedBankId.value === bank.id ? 'text-blue-700' : 'text-gray-900'
                            }`}
                          >
                            {bank.name}
                          </h3>
                          <p class="mt-1 text-xs text-gray-600 wrap-break-word">
                            {bank.description}
                          </p>
                        </div>
                        <button
                          class="opacity-0 text-gray-400 hover:text-red-600 group-hover:opacity-100 transition-opacity"
                          onClick={(e) => {
                            e.stopPropagation()
                            toggleDeleteWarning(bank.id)
                          }}
                        >
                          <Trash class="h-5 w-5" />
                        </button>

                        <button
                          class="opacity-0 text-gray-400 hover:text-primary-600 group-hover:opacity-100 transition-opacity"
                          onClick={(e) => {
                            e.stopPropagation()
                            onEditClick(bank.id)
                          }}
                        >
                          <Pencil class="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Content - Data Table */}
            <div class="col-span-9">
              {selectedBank.value ? (
                <DataTable
                  title={selectedBank.value.name}
                  subtitle={selectedBank.value.description}
                  columns={columns}
                  data={currentQuestions.value}
                  total={questionTotalCount.value}
                  page={questionPage.value}
                  pageSize={questionPageSize.value}
                  onChange={handleChange}
                  onEdit={(row) => handleEditQuestion(row as Question)}
                  onDelete={(row) => handleDeleteQuestion(row as Question)}
                >
                  {{
                    headerAction: () => (
                      <div class="flex flex-wrap gap-3">
                        {/* Search Input */}
                        <div class="relative min-w-0 flex-1">
                          <input
                            type="text"
                            placeholder="Search questions..."
                            class="w-full rounded-lg border border-gray-300 px-4 py-2 pr-28 focus:border-blue-500 focus:outline-none"
                            value={questionSearch.value}
                            onInput={(e: any) => (questionSearch.value = e.target.value)}
                            onKeyup={(e: KeyboardEvent) => e.key === 'Enter' && handleSearch()}
                          />
                          <Button
                            variant="primary"
                            size="sm"
                            class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-blue-600 hover:bg-transparent"
                            onClick={() => handleSearch()}
                            icon={() => <Search class="h-4 w-4" />}
                            iconPosition="right"
                          >
                            Search
                          </Button>
                        </div>
                        {/* Add Question Button */}
                        <button
                          class="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                          onClick={() => onAddNewQuestion()}
                        >
                          Add Question
                        </button>
                      </div>
                    ),
                  }}
                </DataTable>
              ) : (
                <div class="rounded-2xl bg-white p-12 text-center shadow-sm">
                  <p class="text-gray-500">Select a bank to view questions</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Modals */}
        <AddBankModal
          show={showAddBankModal.value}
          bank={editingBank.value}
          onClose={() => {
            showAddBankModal.value = false
            editingBank.value = null
          }}
          onCreate={handleCreateBank}
          onUpdate={handleUpdateBank}
        />

        <AddQuestionModal
          title={selectedBank.value?.name}
          show={showAddQuestionModal.value}
          question={editingQuestion.value}
          onClose={() => {
            showAddQuestionModal.value = false
            editingQuestion.value = null
          }}
          onCreate={handleCreateQuestion}
          onUpdate={handleUpdateQuestion}
        />

        <DeleteConfirmModal
          show={showDeleteConfirmModal.value}
          onCancel={closeDeleteModal}
          onConfirm={confirmDeleteBank}
          title="Delete Question Bank"
          message="Are you sure you want to delete this question bank? This action cannot be undone."
        />
      </div>
    )
  },
})
