import { useState } from 'react'
import { RVA311_CATEGORIES } from '../config'

export default function CategoryGrid({ lang, onCategorySelect }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedCategory, setExpandedCategory] = useState(null)

  const filteredCategories = RVA311_CATEGORIES.filter(cat => {
    const name = lang === 'es' ? cat.nameEs : cat.name
    return name.toLowerCase().includes(searchTerm.toLowerCase())
  })

  const handleCategoryClick = (category) => {
    if (category.externalUrl) {
      window.open(category.externalUrl, '_blank')
      return
    }
    if (category.subcategories) {
      setExpandedCategory(expandedCategory === category.id ? null : category.id)
    } else {
      onCategorySelect(category)
    }
  }

  const handleSubcategoryClick = (subcategory, parentCategory) => {
    const fullCategory = {
      ...parentCategory,
      ...subcategory,
      parentName: parentCategory.name,
      parentNameEs: parentCategory.nameEs
    }
    onCategorySelect(fullCategory)
  }

  return (
    <div>
      <h1 className="page-title">
        {lang === 'es' ? 'Solicitar Servicio' : 'Request a Service'}
      </h1>
      <p className="page-subtitle">
        {lang === 'es'
          ? 'Seleccione la categoría que mejor describe su solicitud'
          : 'Select the category that best describes your request'
        }
      </p>

      <div className="search-bar">
        <input
          type="text"
          className="search-input"
          placeholder={lang === 'es' ? 'Buscar tipo de solicitud...' : 'Search for Request Type...'}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="category-grid">
        {filteredCategories.map(category => (
          <div
            key={category.id}
            className={`category-card ${category.subcategories ? 'expandable' : ''}`}
          >
            <div
              onClick={() => handleCategoryClick(category)}
              style={{ cursor: 'pointer' }}
            >
              <div className="category-icon">{category.icon}</div>
              <div className="category-name">
                {lang === 'es' ? category.nameEs : category.name}
                {category.isNew && <span className="badge-new">NEW</span>}
                {category.webOnly && <span className="badge-web-only">{lang === 'es' ? 'Solo en línea' : 'Online Only'}</span>}
              </div>
              <div className="category-description">
                {category.description}
              </div>
            </div>

            {category.subcategories && expandedCategory === category.id && (
              <div className="subcategory-list">
                {category.subcategories.map(sub => (
                  <div
                    key={sub.id}
                    className="subcategory-item"
                    onClick={() => handleSubcategoryClick(sub, category)}
                  >
                    <div className="subcategory-name">
                      {lang === 'es' ? sub.nameEs : sub.name}
                    </div>
                    <div className="subcategory-description">
                      {sub.description}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
